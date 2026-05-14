import { computed, ref, shallowRef, type Ref } from 'vue'
import type { AuthorFilter, AuthorStats } from './types'
import { useAuthorsMetadata, AUTHORS_STORAGE } from './useMetadataLoader'
import { getValidatedMetadata, setMetadata } from './useCache'
import { escapeLike, queryFirst, queryRows, queryScalar } from './useSQLiteDatabase'

const STORAGE_VERSION = 1
const authorsCache = shallowRef<Map<number, AuthorStats[]>>(new Map())
const loadedAuthorChunkIds: Ref<number[]> = ref([])

async function initLoadedAuthorChunkIds() {
  const meta = await getValidatedMetadata(AUTHORS_STORAGE, STORAGE_VERSION, { autoClean: true })
  loadedAuthorChunkIds.value = meta?.loadedChunkIds ?? []
}
void initLoadedAuthorChunkIds()

interface AuthorRow {
  author: string
  poem_count: number
  poem_ids_json: string
  poem_type_counts_json: string
  meter_patterns_json: string
  word_frequency_json: string
  similar_authors_json: string
  chunk_id: number
}

function parseJson<T>(value: string, fallback: T): T {
  try {
    return value ? JSON.parse(value) as T : fallback
  } catch {
    return fallback
  }
}

function toAuthor(row: AuthorRow): AuthorStats {
  return {
    author: row.author,
    poem_count: row.poem_count,
    poem_ids: parseJson(row.poem_ids_json, [] as string[]),
    poem_type_counts: parseJson(row.poem_type_counts_json, {} as Record<string, number>),
    meter_patterns: parseJson(row.meter_patterns_json, [] as Array<{ pattern: string; count: number }>),
    word_frequency: parseJson(row.word_frequency_json, {} as Record<string, number>),
    similar_authors: parseJson(row.similar_authors_json, [] as Array<{ author: string; similarity: number }>)
  }
}

function buildWhere(filter?: AuthorFilter) {
  const clauses: string[] = []
  const params: Array<string | number> = []

  if (filter?.minPoems !== undefined) {
    clauses.push('poem_count >= ?')
    params.push(filter.minPoems)
  }
  if (filter?.maxPoems !== undefined) {
    clauses.push('poem_count <= ?')
    params.push(filter.maxPoems)
  }
  if (filter?.search) {
    clauses.push("author LIKE ? ESCAPE '\\\\'")
    params.push(`%${escapeLike(filter.search)}%`)
  }

  return {
    whereSql: clauses.length > 0 ? `WHERE ${clauses.join(' AND ')}` : '',
    params
  }
}

async function markLoadedChunk(chunkId: number, totalChunks: number) {
  if (loadedAuthorChunkIds.value.includes(chunkId)) return
  loadedAuthorChunkIds.value = [...loadedAuthorChunkIds.value, chunkId]
  await setMetadata(AUTHORS_STORAGE, {
    loadedChunkIds: [...loadedAuthorChunkIds.value],
    totalChunks,
    version: STORAGE_VERSION
  })
}

export function useAuthors() {
  const { metadata: authorsIndex, loading, error, loadMetadata } = useAuthorsMetadata()

  const totalAuthors = computed(() => authorsIndex.value?.totalAuthors || 0)
  const totalChunks = computed(() => authorsIndex.value?.total || 0)
  const loadedChunkCount = computed(() => loadedAuthorChunkIds.value.length)

  async function loadAuthorChunk(chunkId: number): Promise<AuthorStats[]> {
    if (authorsCache.value.has(chunkId)) {
      return authorsCache.value.get(chunkId)!
    }

    const rows = await queryRows<AuthorRow>(
      `SELECT author, poem_count, poem_ids_json, poem_type_counts_json, meter_patterns_json,
              word_frequency_json, similar_authors_json, chunk_id
       FROM authors
       WHERE chunk_id = ?
       ORDER BY poem_count DESC, author ASC`,
      [chunkId]
    )

    const authors = rows.map(toAuthor)
    authorsCache.value.set(chunkId, authors)
    await markLoadedChunk(chunkId, totalChunks.value)
    return authors
  }

  async function loadAllAuthors(progressCallback?: (loaded: number, total: number) => void): Promise<AuthorStats[]> {
    const meta = await loadMetadata()
    const allAuthors: AuthorStats[] = []

    for (let index = 0; index < meta.chunks.length; index++) {
      allAuthors.push(...await loadAuthorChunk(index))
      progressCallback?.(index + 1, meta.chunks.length)
    }

    return allAuthors
  }

  async function getAuthorByName(name: string): Promise<AuthorStats | null> {
    const row = await queryFirst<AuthorRow>(
      `SELECT author, poem_count, poem_ids_json, poem_type_counts_json, meter_patterns_json,
              word_frequency_json, similar_authors_json, chunk_id
       FROM authors
       WHERE author = ?`,
      [name]
    )
    return row ? toAuthor(row) : null
  }

  async function getAuthorsByChunk(chunkId: number): Promise<AuthorStats[]> {
    return loadAuthorChunk(chunkId)
  }

  async function queryAuthors(filter?: AuthorFilter, page: number = 1, pageSize: number = 24) {
    const { whereSql, params } = buildWhere(filter)
    const offset = Math.max(0, (page - 1) * pageSize)
    const filteredTotal = Number(
      (await queryScalar<number>(`SELECT COUNT(*) AS total FROM authors ${whereSql}`, params)) ?? 0
    )
    const rows = await queryRows<AuthorRow>(
      `SELECT author, poem_count, poem_ids_json, poem_type_counts_json, meter_patterns_json,
              word_frequency_json, similar_authors_json, chunk_id
       FROM authors
       ${whereSql}
       ORDER BY poem_count DESC, author ASC
       LIMIT ? OFFSET ?`,
      [...params, pageSize, offset]
    )

    return {
      authors: rows.map(toAuthor),
      total: totalAuthors.value,
      filteredTotal,
      page,
      pageSize,
      hasMore: offset + rows.length < filteredTotal
    }
  }

  async function getTopAuthors(limit: number = 20): Promise<AuthorStats[]> {
    const rows = await queryRows<AuthorRow>(
      `SELECT author, poem_count, poem_ids_json, poem_type_counts_json, meter_patterns_json,
              word_frequency_json, similar_authors_json, chunk_id
       FROM authors
       ORDER BY poem_count DESC, author ASC
       LIMIT ?`,
      [limit]
    )
    return rows.map(toAuthor)
  }

  async function getSimilarAuthors(authorName: string) {
    const author = await getAuthorByName(authorName)
    return author?.similar_authors ?? []
  }

  async function getAuthorWordFrequency(authorName: string) {
    const author = await getAuthorByName(authorName)
    return author?.word_frequency ?? {}
  }

  async function getAuthorPoemTypes(authorName: string) {
    const author = await getAuthorByName(authorName)
    return author?.poem_type_counts ?? {}
  }

  function getLoadedAuthors() {
    return Array.from(authorsCache.value.values()).flat()
  }

  async function preloadChunks(chunkIds: number[]) {
    await Promise.all(chunkIds.map(chunkId => loadAuthorChunk(chunkId)))
  }

  async function clearCache() {
    authorsCache.value.clear()
    loadedAuthorChunkIds.value = []
  }

  return {
    metadata: authorsIndex,
    totalAuthors,
    totalChunks,
    loadedChunkCount,
    loading,
    error,
    loadMetadata,
    loadAuthorChunk,
    loadAllAuthors,
    getAuthorByName,
    getAuthorsByChunk,
    queryAuthors,
    getTopAuthors,
    getSimilarAuthors,
    getAuthorWordFrequency,
    getAuthorPoemTypes,
    getLoadedAuthors,
    preloadChunks,
    clearCache
  }
}
