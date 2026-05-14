import { computed, ref, shallowRef, type Ref } from 'vue'
import type { PoemIndexManifest, PoemSummary, SearchResult, SearchResultSet } from './types'
import { usePoemIndexManifest, POEM_INDEX_STORAGE } from './useMetadataLoader'
import { getValidatedMetadata, setCache, setMetadata } from './useCache'
import { escapeLike, queryRows, queryScalar } from './useSQLiteDatabase'

const STORAGE_VERSION = 1
const poemChunkCache = shallowRef<Map<string, Map<string, PoemSummary>>>(new Map())
const loadedPrefixes: Ref<Set<string>> = ref(new Set())

async function initLoadedPrefixes() {
  const meta = await getValidatedMetadata(POEM_INDEX_STORAGE, STORAGE_VERSION, { autoClean: true })
  loadedPrefixes.value = meta ? new Set(meta.loadedChunkIds.map(code => String.fromCharCode(code))) : new Set()
}
void initLoadedPrefixes()

interface PoemRow {
  id: string
  title: string
  author: string
  dynasty: string
  genre: string
  chunk_id: number
}

function toSummary(row: PoemRow): PoemSummary {
  return {
    id: row.id,
    title: row.title,
    author: row.author,
    dynasty: row.dynasty,
    genre: row.genre,
    chunk_id: row.chunk_id
  }
}

function toSearchResult(row: PoemRow, score: number): SearchResult {
  return {
    id: row.id,
    title: row.title,
    author: row.author,
    dynasty: row.dynasty,
    score
  }
}

async function rememberPrefix(prefix: string, totalPrefixes: number) {
  if (loadedPrefixes.value.has(prefix)) return
  loadedPrefixes.value = new Set([...loadedPrefixes.value, prefix])
  const prefixesArray = [...loadedPrefixes.value]
  await setCache(POEM_INDEX_STORAGE, 'loaded-prefixes', prefixesArray)
  await setMetadata(POEM_INDEX_STORAGE, {
    loadedChunkIds: prefixesArray.map(item => item.charCodeAt(0)),
    totalChunks: totalPrefixes,
    version: STORAGE_VERSION
  })
}

export function useSearchIndex() {
  const { metadata: manifest, loading, error, loadMetadata } = usePoemIndexManifest()

  const totalPoems = computed(() => manifest.value?.metadata?.total || 0)
  const totalIndexFiles = computed(() => manifest.value?.metadata?.indexFiles || 0)

  async function loadPoemChunk(prefix: string): Promise<Map<string, PoemSummary> | null> {
    if (poemChunkCache.value.has(prefix)) {
      return poemChunkCache.value.get(prefix)!
    }

    const manifestData = await loadMetadata()
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       WHERE lower(substr(id, 1, 2)) = ?
       ORDER BY id`,
      [prefix.toLowerCase()]
    )

    if (rows.length === 0) return null

    const poemMap = new Map(rows.map(row => {
      const poem = toSummary(row)
      return [poem.id, poem] as const
    }))

    poemChunkCache.value.set(prefix, poemMap)
    await rememberPrefix(prefix, Object.keys(manifestData.prefixMap).length)
    return poemMap
  }

  async function searchPoemById(id: string): Promise<PoemSummary | null> {
    const chunk = await loadPoemChunk(id.substring(0, 2).toLowerCase())
    return chunk?.get(id) || null
  }

  async function getPoemSummaryById(id: string): Promise<PoemSummary | null> {
    return searchPoemById(id)
  }

  async function getPoemSummariesByIds(ids: string[]): Promise<Map<string, PoemSummary>> {
    if (ids.length === 0) return new Map()
    const placeholders = ids.map(() => '?').join(', ')
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       WHERE id IN (${placeholders})`,
      ids
    )
    return new Map(rows.map(row => {
      const poem = toSummary(row)
      return [poem.id, poem] as const
    }))
  }

  async function searchByKeyword(keyword: string, options?: { dynasty?: string; genre?: string; limit?: number }): Promise<SearchResult[]> {
    const clauses = ["(title LIKE ? ESCAPE '\\\\' OR author LIKE ? ESCAPE '\\\\' OR id LIKE ? ESCAPE '\\\\' OR sentences_text LIKE ? ESCAPE '\\\\')"]
    const likeKeyword = `%${escapeLike(keyword)}%`
    const params: Array<string | number> = [likeKeyword, likeKeyword, likeKeyword, likeKeyword]

    if (options?.dynasty) {
      clauses.push('dynasty = ?')
      params.push(options.dynasty)
    }
    if (options?.genre) {
      clauses.push('genre = ?')
      params.push(options.genre)
    }

    const limit = options?.limit ?? 50
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       WHERE ${clauses.join(' AND ')}
       ORDER BY chunk_id, id
       LIMIT ?`,
      [...params, limit]
    )

    return rows.map(row => toSearchResult(row, 1))
  }

  async function searchPoems(query: string, page: number = 1, pageSize: number = 20): Promise<SearchResultSet> {
    const likeQuery = `%${escapeLike(query)}%`
    const whereSql = "(title LIKE ? ESCAPE '\\\\' OR author LIKE ? ESCAPE '\\\\' OR id LIKE ? ESCAPE '\\\\' OR sentences_text LIKE ? ESCAPE '\\\\')"
    const params = [likeQuery, likeQuery, likeQuery, likeQuery]
    const total = Number((await queryScalar<number>(`SELECT COUNT(*) AS total FROM poems WHERE ${whereSql}`, params)) ?? 0)
    const offset = Math.max(0, (page - 1) * pageSize)
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       WHERE ${whereSql}
       ORDER BY chunk_id, id
       LIMIT ? OFFSET ?`,
      [...params, pageSize, offset]
    )

    return {
      results: rows.map(row => toSearchResult(row, 1)),
      total,
      page,
      pageSize,
      hasMore: offset + rows.length < total
    }
  }

  async function searchMultipleKeywords(keywords: string[], options?: { matchAll?: boolean; dynasty?: string; genre?: string }): Promise<SearchResult[]> {
    const results = await Promise.all(keywords.map(keyword => searchByKeyword(keyword, { dynasty: options?.dynasty, genre: options?.genre, limit: 100 })))
    const merged = new Map<string, SearchResult>()

    for (const batch of results) {
      for (const item of batch) {
        const existing = merged.get(item.id)
        if (existing) {
          existing.score += item.score
        } else {
          merged.set(item.id, { ...item })
        }
      }
    }

    let list = [...merged.values()]
    if (options?.matchAll) {
      const required = keywords.length
      const counts = new Map<string, number>()
      for (const batch of results) {
        for (const item of batch) {
          counts.set(item.id, (counts.get(item.id) ?? 0) + 1)
        }
      }
      list = list.filter(item => counts.get(item.id) === required)
    }

    return list.sort((a, b) => b.score - a.score).slice(0, 100)
  }

  async function getPoemsByPrefix(prefix: string, limit?: number): Promise<PoemSummary[]> {
    const chunk = await loadPoemChunk(prefix)
    const poems = chunk ? [...chunk.values()] : []
    return limit ? poems.slice(0, limit) : poems
  }

  async function getPoemsByAuthor(author: string, limit: number = 50): Promise<SearchResult[]> {
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       WHERE author = ?
       ORDER BY chunk_id, id
       LIMIT ?`,
      [author, limit]
    )
    return rows.map(row => toSearchResult(row, 1))
  }

  async function getPoemsByDynasty(dynasty: string, page: number = 1, pageSize: number = 20): Promise<SearchResultSet> {
    const total = Number((await queryScalar<number>('SELECT COUNT(*) AS total FROM poems WHERE dynasty = ?', [dynasty])) ?? 0)
    const offset = Math.max(0, (page - 1) * pageSize)
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       WHERE dynasty = ?
       ORDER BY chunk_id, id
       LIMIT ? OFFSET ?`,
      [dynasty, pageSize, offset]
    )
    return {
      results: rows.map(row => toSearchResult(row, 1)),
      total,
      page,
      pageSize,
      hasMore: offset + rows.length < total
    }
  }

  function getLoadedPrefixCount(): number {
    return loadedPrefixes.value.size
  }

  async function preloadPrefixes(prefixes: string[]): Promise<void> {
    await Promise.all(prefixes.map(prefix => loadPoemChunk(prefix)))
  }

  async function clearCache(): Promise<void> {
    poemChunkCache.value.clear()
    loadedPrefixes.value = new Set()
  }

  return {
    metadata: manifest,
    totalPoems,
    totalIndexFiles,
    loadedPrefixCount: computed(() => loadedPrefixes.value.size),
    loading,
    error,
    loadMetadata,
    loadPoemChunk,
    searchPoemById,
    getPoemSummaryById,
    getPoemSummariesByIds,
    searchByKeyword,
    searchPoems,
    searchMultipleKeywords,
    getPoemsByPrefix,
    getPoemsByAuthor,
    getPoemsByDynasty,
    getLoadedPrefixCount,
    preloadPrefixes,
    clearCache
  }
}
