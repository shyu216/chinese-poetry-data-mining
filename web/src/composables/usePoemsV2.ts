import { ref, shallowRef, computed, type Ref } from 'vue'
import type {
  PoemSummary,
  PoemDetail,
  PoemFilter,
  PoemChunkMeta,
  PoemsIndex,
  PoemQueryResult
} from './types'
import { usePoemsMetadata, POEMS_STORAGE, parseCsvLine, getChunkUrl } from './useMetadataLoader'
import { getCache, setCache, getChunkedCache, setChunkedCache, getMetadata, setMetadata } from './useCacheV2'

// Separate storage keys for summaries and details to avoid cache conflicts
const POEMS_SUMMARY_STORAGE = 'poems-summary-v2'
const POEMS_DETAIL_STORAGE = 'poems-detail-v2'

const poemSummaryCache = shallowRef<Map<number, PoemSummary[]>>(new Map())
const poemDetailCache = shallowRef<Map<number, Map<string, PoemDetail>>>(new Map())
const loadedChunkIds: Ref<number[]> = ref([])
const indexLoading: Ref<boolean> = ref(false)

async function initLoadedChunkIds() {
  const meta = await getMetadata(POEMS_STORAGE)
  if (meta) {
    loadedChunkIds.value = meta.loadedChunkIds
  }
}
initLoadedChunkIds()

export function usePoemsV2() {
  const { metadata: poemsIndex, loading: indexLoading, error: indexError, loadMetadata } = usePoemsMetadata()

  const totalPoems = computed(() => poemsIndex.value?.metadata?.total || 0)
  const totalChunks = computed(() => poemsIndex.value?.metadata?.chunks || 0)
  const dynasties = computed(() => poemsIndex.value?.stats?.dynasties || [])
  const genres = computed(() => poemsIndex.value?.stats?.genres || [])

  const loadedChunkCount = computed(() => loadedChunkIds.value.length)

  async function loadChunkSummaries(chunkNum: number): Promise<PoemSummary[]> {
    if (poemSummaryCache.value.has(chunkNum)) {
      return poemSummaryCache.value.get(chunkNum)!
    }

    const cached = await getChunkedCache<PoemSummary[]>(POEMS_SUMMARY_STORAGE, chunkNum)
    if (cached) {
      poemSummaryCache.value.set(chunkNum, cached)
      return cached
    }

    const chunkId = chunkNum.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/poems_chunk_${chunkId}.csv`)
    if (!response.ok) throw new Error(`Failed to load chunk ${chunkNum}`)

    const csvText = await response.text()
    const lines = csvText.trim().split('\n')
    const dataLines = lines.slice(1)

    const poems: PoemSummary[] = []

    for (const line of dataLines) {
      const cols = parseCsvLine(line)
      if (cols.length < 5) continue

      const [id, title, author, dynasty, genre] = cols

      poems.push({
        id: id || '',
        title: title || '',
        author: author || '佚名',
        dynasty: dynasty || '',
        genre: genre || ''
      })
    }

    poemSummaryCache.value.set(chunkNum, poems)
    await setChunkedCache(POEMS_SUMMARY_STORAGE, chunkNum, poems)

    if (!loadedChunkIds.value.includes(chunkNum)) {
      loadedChunkIds.value.push(chunkNum)
      await setMetadata(POEMS_STORAGE, { loadedChunkIds: [...loadedChunkIds.value], totalChunks: totalChunks.value })
    }

    return poems
  }

  async function loadChunkDetails(chunkNum: number): Promise<Map<string, PoemDetail>> {
    if (poemDetailCache.value.has(chunkNum)) {
      return poemDetailCache.value.get(chunkNum)!
    }

    const cached = await getChunkedCache<Record<string, PoemDetail>>(POEMS_DETAIL_STORAGE, chunkNum)
    if (cached) {
      const poemMap = new Map<string, PoemDetail>(Object.entries(cached))
      poemDetailCache.value.set(chunkNum, poemMap)
      return poemMap
    }

    const chunkId = chunkNum.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/poems_chunk_${chunkId}.csv`)
    if (!response.ok) throw new Error(`Failed to load chunk ${chunkNum}`)

    const csvText = await response.text()
    const lines = csvText.trim().split('\n')
    const dataLines = lines.slice(1)

    const poemMap = new Map<string, PoemDetail>()

    for (const line of dataLines) {
      const cols = parseCsvLine(line)
      if (cols.length < 10) continue

      const [id, title, author, dynasty, genre, poemType, sentences, meterPattern, hash, words] = cols
      const poemId = id || ''

      poemMap.set(poemId, {
        id: poemId,
        title: title || '',
        author: author || '佚名',
        dynasty: dynasty || '',
        genre: genre || '',
        poem_type: poemType,
        meter_pattern: meterPattern,
        sentences: sentences ? sentences.split(' ').filter(s => s) : [],
        words: words ? words.split(' ').filter(w => w) : [],
        hash: hash || ''
      })
    }

    poemDetailCache.value.set(chunkNum, poemMap)
    await setChunkedCache(POEMS_DETAIL_STORAGE, chunkNum, Object.fromEntries(poemMap))

    return poemMap
  }

  async function getPoemById(poemId: string): Promise<PoemDetail | null> {
    for (const [chunkNum, chunkMap] of poemDetailCache.value.entries()) {
      if (chunkMap.has(poemId)) {
        return chunkMap.get(poemId)!
      }
    }

    const index = await loadMetadata()

    for (const chunkInfo of index.chunks) {
      if (poemDetailCache.value.has(chunkInfo.id)) continue

      const chunk = await loadChunkDetails(chunkInfo.id)
      poemDetailCache.value.set(chunkInfo.id, chunk)

      if (chunk.has(poemId)) {
        return chunk.get(poemId)!
      }
    }

    return null
  }

  function getRelevantChunks(filter?: PoemFilter): number[] {
    if (!poemsIndex.value) return []

    return poemsIndex.value.chunks
      .filter(chunk => {
        if (filter?.dynasty && !chunk.dynasties.includes(filter.dynasty)) {
          return false
        }
        if (filter?.genre && !chunk.genres.includes(filter.genre)) {
          return false
        }
        return true
      })
      .map(chunk => chunk.id)
  }

  async function queryPoems(
    filter?: PoemFilter,
    page: number = 1,
    pageSize: number = 24
  ): Promise<PoemQueryResult> {
    const index = await loadMetadata()
    const relevantChunks = getRelevantChunks(filter)

    const poemsPerChunk = 1000
    const startIndex = (page - 1) * pageSize
    const endIndex = startIndex + pageSize

    const startChunkIndex = Math.floor(startIndex / poemsPerChunk)
    const endChunkIndex = Math.floor(endIndex / poemsPerChunk) + 1

    const chunksToLoad = relevantChunks.slice(startChunkIndex, endChunkIndex)
    const allPoems: PoemSummary[] = []

    for (const chunkId of chunksToLoad) {
      const chunkPoems = await loadChunkSummaries(chunkId)
      allPoems.push(...chunkPoems)
    }

    let filtered = allPoems

    if (filter?.search) {
      const searchLower = filter.search.toLowerCase()
      filtered = filtered.filter(p =>
        p.title.toLowerCase().includes(searchLower) ||
        p.author.toLowerCase().includes(searchLower) ||
        p.id.toLowerCase().includes(searchLower)
      )
    }

    if (filter?.author) {
      filtered = filtered.filter(p => p.author === filter.author)
    }

    const paged = filtered.slice(startIndex % poemsPerChunk, (startIndex % poemsPerChunk) + pageSize)

    return {
      poems: paged,
      total: index.metadata.total,
      filteredTotal: filtered.length,
      page,
      pageSize,
      hasMore: endIndex < filtered.length
    }
  }

  async function getPoemsByDynasty(
    dynasty: string,
    page: number = 1,
    pageSize: number = 24
  ): Promise<PoemQueryResult> {
    return queryPoems({ dynasty }, page, pageSize)
  }

  async function getPoemsByGenre(
    genre: string,
    page: number = 1,
    pageSize: number = 24
  ): Promise<PoemQueryResult> {
    return queryPoems({ genre }, page, pageSize)
  }

  async function searchPoems(
    keyword: string,
    page: number = 1,
    pageSize: number = 24
  ): Promise<PoemQueryResult> {
    return queryPoems({ search: keyword }, page, pageSize)
  }

  async function getAllAuthors(): Promise<string[]> {
    const index = await loadMetadata()
    const authorsSet = new Set<string>()

    for (const chunk of index.chunks.slice(0, 10)) {
      const poems = await loadChunkSummaries(chunk.id)
      poems.forEach(p => authorsSet.add(p.author))
    }

    return Array.from(authorsSet).sort()
  }

  function getChunkInfo(chunkId: number): PoemChunkMeta | undefined {
    return poemsIndex.value?.chunks.find(c => c.id === chunkId)
  }

  function getChunkStats() {
    if (!poemsIndex.value) return null

    const stats: Record<string, { count: number; poems: number }> = {}

    for (const chunk of poemsIndex.value.chunks) {
      for (const dynasty of chunk.dynasties) {
        if (!stats[dynasty]) {
          stats[dynasty] = { count: 0, poems: 0 }
        }
        stats[dynasty].count++
        stats[dynasty].poems += chunk.count
      }
    }

    return stats
  }

  async function preloadChunks(chunkIds: number[]): Promise<void> {
    await Promise.all(chunkIds.map(id => loadChunkSummaries(id)))
  }

  async function clearCache(): Promise<void> {
    poemSummaryCache.value.clear()
    poemDetailCache.value.clear()
    loadedChunkIds.value = []
  }

  return {
    metadata: poemsIndex,
    totalPoems,
    totalChunks,
    loadedChunkCount,
    dynasties,
    genres,
    indexLoading,
    loadMetadata,
    loadChunkSummaries,
    loadChunkDetails,
    getPoemById,
    queryPoems,
    getPoemsByDynasty,
    getPoemsByGenre,
    searchPoems,
    getAllAuthors,
    getChunkInfo,
    getChunkStats,
    preloadChunks,
    clearCache
  }
}
