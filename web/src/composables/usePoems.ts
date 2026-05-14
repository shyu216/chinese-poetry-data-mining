import { computed, ref, shallowRef, type Ref } from 'vue'
import type { PoemDetail, PoemFilter, PoemQueryResult, PoemSummary } from './types'
import { usePoemsMetadata, POEMS_STORAGE } from './useMetadataLoader'
import { getValidatedMetadata, setMetadata } from './useCache'
import { escapeLike, queryFirst, queryRows, queryScalar } from './useSQLiteDatabase'

export const POEMS_SUMMARY_STORAGE = 'poems-summary-v2'
const POEMS_DETAIL_STORAGE = 'poems-detail-v2'
const STORAGE_VERSION = 1

const poemSummaryCache = shallowRef<Map<number, PoemSummary[]>>(new Map())
const poemDetailCache = shallowRef<Map<number, Map<string, PoemDetail>>>(new Map())
const loadedChunkIds: Ref<number[]> = ref([])
const loadedSummaryChunkIds: Ref<number[]> = ref([])
const loadedDetailChunkIds: Ref<number[]> = ref([])

async function initLoadedChunkIds() {
  const [poemsMeta, summaryMeta, detailMeta] = await Promise.all([
    getValidatedMetadata(POEMS_STORAGE, STORAGE_VERSION, { autoClean: true }),
    getValidatedMetadata(POEMS_SUMMARY_STORAGE, STORAGE_VERSION, { autoClean: true }),
    getValidatedMetadata(POEMS_DETAIL_STORAGE, STORAGE_VERSION, { autoClean: true })
  ])

  loadedChunkIds.value = poemsMeta?.loadedChunkIds ?? []
  loadedSummaryChunkIds.value = summaryMeta?.loadedChunkIds ?? []
  loadedDetailChunkIds.value = detailMeta?.loadedChunkIds ?? []
}
void initLoadedChunkIds()

interface PoemRow {
  id: string
  title: string
  author: string
  dynasty: string
  genre: string
  poem_type: string | null
  sentences_text: string
  meter_pattern: string | null
  hash: string
  words_text: string
  chunk_id: number
}

function toSummary(row: Pick<PoemRow, 'id' | 'title' | 'author' | 'dynasty' | 'genre' | 'chunk_id'>): PoemSummary {
  return {
    id: row.id,
    title: row.title,
    author: row.author,
    dynasty: row.dynasty,
    genre: row.genre,
    chunk_id: row.chunk_id
  }
}

function splitText(value: string) {
  return value ? value.split(' ').filter(Boolean) : []
}

function toDetail(row: PoemRow): PoemDetail {
  return {
    ...toSummary(row),
    poem_type: row.poem_type ?? '',
    meter_pattern: row.meter_pattern ?? '',
    sentences: splitText(row.sentences_text),
    words: splitText(row.words_text),
    hash: row.hash
  }
}

function buildWhere(filter?: PoemFilter) {
  const clauses: string[] = []
  const params: Array<string | number> = []

  if (filter?.dynasty) {
    clauses.push('dynasty = ?')
    params.push(filter.dynasty)
  }
  if (filter?.genre) {
    clauses.push('genre = ?')
    params.push(filter.genre)
  }
  if (filter?.author) {
    clauses.push('author = ?')
    params.push(filter.author)
  }
  if (filter?.title) {
    clauses.push("title LIKE ? ESCAPE '\\\\'")
    params.push(`%${escapeLike(filter.title)}%`)
  }
  if (filter?.search) {
    const keyword = `%${escapeLike(filter.search)}%`
    clauses.push("(title LIKE ? ESCAPE '\\\\' OR author LIKE ? ESCAPE '\\\\' OR id LIKE ? ESCAPE '\\\\' OR sentences_text LIKE ? ESCAPE '\\\\')")
    params.push(keyword, keyword, keyword, keyword)
  }

  return {
    whereSql: clauses.length > 0 ? `WHERE ${clauses.join(' AND ')}` : '',
    params
  }
}

async function markLoadedChunk(chunkId: number, storage: string, loadedIds: Ref<number[]>, totalChunks: number) {
  if (loadedIds.value.includes(chunkId)) return
  loadedIds.value = [...loadedIds.value, chunkId]
  if (!loadedChunkIds.value.includes(chunkId)) {
    loadedChunkIds.value = [...loadedChunkIds.value, chunkId]
    await setMetadata(POEMS_STORAGE, {
      loadedChunkIds: [...loadedChunkIds.value],
      totalChunks,
      version: STORAGE_VERSION
    })
  }
  await setMetadata(storage, {
    loadedChunkIds: [...loadedIds.value],
    totalChunks,
    version: STORAGE_VERSION
  })
}

export function usePoems() {
  const { metadata: poemsIndex, loading, error, loadMetadata } = usePoemsMetadata()

  const totalPoems = computed(() => poemsIndex.value?.metadata?.total || 0)
  const totalChunks = computed(() => poemsIndex.value?.metadata?.chunks || 0)
  const dynasties = computed(() => poemsIndex.value?.stats?.dynasties || [])
  const genres = computed(() => poemsIndex.value?.stats?.genres || [])
  const poemCounts = computed(() => poemsIndex.value?.stats?.counts || { songshi: 0, songci: 0, tangshi: 0 })
  const loadedChunkCount = computed(() => loadedChunkIds.value.length)

  async function loadChunkSummaries(chunkNum: number): Promise<PoemSummary[]> {
    if (poemSummaryCache.value.has(chunkNum)) {
      return poemSummaryCache.value.get(chunkNum)!
    }

    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       WHERE chunk_id = ?
       ORDER BY id`,
      [chunkNum]
    )
    const poems = rows.map(toSummary)
    poemSummaryCache.value.set(chunkNum, poems)
    await markLoadedChunk(chunkNum, POEMS_SUMMARY_STORAGE, loadedSummaryChunkIds, totalChunks.value)
    return poems
  }

  async function loadChunkDetails(chunkNum: number): Promise<Map<string, PoemDetail>> {
    if (poemDetailCache.value.has(chunkNum)) {
      return poemDetailCache.value.get(chunkNum)!
    }

    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, poem_type, sentences_text, meter_pattern, hash, words_text, chunk_id
       FROM poems
       WHERE chunk_id = ?
       ORDER BY id`,
      [chunkNum]
    )

    const poemMap = new Map(rows.map(row => {
      const detail = toDetail(row)
      return [detail.id, detail] as const
    }))

    poemDetailCache.value.set(chunkNum, poemMap)
    await markLoadedChunk(chunkNum, POEMS_DETAIL_STORAGE, loadedDetailChunkIds, totalChunks.value)
    return poemMap
  }

  async function getPoemById(poemId: string, chunkId?: number): Promise<PoemDetail | null> {
    if (chunkId !== undefined && poemDetailCache.value.has(chunkId)) {
      return poemDetailCache.value.get(chunkId)?.get(poemId) ?? null
    }

    for (const chunk of poemDetailCache.value.values()) {
      const cached = chunk.get(poemId)
      if (cached) return cached
    }

    const row = chunkId !== undefined
      ? await queryFirst<PoemRow>(
          `SELECT id, title, author, dynasty, genre, poem_type, sentences_text, meter_pattern, hash, words_text, chunk_id
           FROM poems
           WHERE id = ? AND chunk_id = ?`,
          [poemId, chunkId]
        )
      : await queryFirst<PoemRow>(
          `SELECT id, title, author, dynasty, genre, poem_type, sentences_text, meter_pattern, hash, words_text, chunk_id
           FROM poems
           WHERE id = ?`,
          [poemId]
        )

    if (!row && chunkId !== undefined) {
      return getPoemById(poemId)
    }

    return row ? toDetail(row) : null
  }

  async function getPoemsByIds(poemIds: string[], _chunkIds?: number[]): Promise<PoemDetail[]> {
    if (poemIds.length === 0) return []

    const placeholders = poemIds.map(() => '?').join(', ')
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, poem_type, sentences_text, meter_pattern, hash, words_text, chunk_id
       FROM poems
       WHERE id IN (${placeholders})`,
      poemIds
    )

    const rowMap = new Map(rows.map(row => [row.id, toDetail(row)]))
    return poemIds.map(id => rowMap.get(id)).filter((row): row is PoemDetail => !!row)
  }

  async function queryPoems(filter?: PoemFilter, page: number = 1, pageSize: number = 24): Promise<PoemQueryResult> {
    const { whereSql, params } = buildWhere(filter)
    const offset = Math.max(0, (page - 1) * pageSize)
    const filteredTotal = Number(
      (await queryScalar<number>(`SELECT COUNT(*) AS total FROM poems ${whereSql}`, params)) ?? 0
    )

    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       ${whereSql}
       ORDER BY chunk_id, id
       LIMIT ? OFFSET ?`,
      [...params, pageSize, offset]
    )

    return {
      poems: rows.map(toSummary),
      total: totalPoems.value,
      filteredTotal,
      page,
      pageSize,
      hasMore: offset + rows.length < filteredTotal
    }
  }

  async function loadAllSummaries(): Promise<PoemSummary[]> {
    const rows = await queryRows<PoemRow>(
      'SELECT id, title, author, dynasty, genre, chunk_id FROM poems ORDER BY chunk_id, id'
    )
    return rows.map(toSummary)
  }

  async function getPoemsByDynasty(dynasty: string, page: number = 1, pageSize: number = 24) {
    return queryPoems({ dynasty }, page, pageSize)
  }

  async function getPoemsByGenre(genre: string, page: number = 1, pageSize: number = 24) {
    return queryPoems({ genre }, page, pageSize)
  }

  async function searchPoemsByKeyword(keyword: string, page: number = 1, pageSize: number = 24) {
    return queryPoems({ search: keyword }, page, pageSize)
  }

  function getLoadedPoems(): PoemSummary[] {
    return Array.from(poemSummaryCache.value.values()).flat()
  }

  async function preloadChunks(chunkIds: number[]): Promise<void> {
    await Promise.all(chunkIds.map(chunkId => loadChunkDetails(chunkId)))
  }

  async function clearCache(): Promise<void> {
    poemSummaryCache.value.clear()
    poemDetailCache.value.clear()
    loadedChunkIds.value = []
    loadedSummaryChunkIds.value = []
    loadedDetailChunkIds.value = []
  }

  return {
    metadata: poemsIndex,
    totalPoems,
    totalChunks,
    dynasties,
    genres,
    poemCounts,
    loadedChunkCount,
    loading,
    error,
    loadMetadata,
    loadChunkSummaries,
    loadChunkDetails,
    getPoemById,
    getPoemsByIds,
    queryPoems,
    loadAllSummaries,
    getPoemsByDynasty,
    getPoemsByGenre,
    searchPoemsByKeyword,
    getLoadedPoems,
    preloadChunks,
    clearCache
  }
}
