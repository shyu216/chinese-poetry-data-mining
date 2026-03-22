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
const loadedSummaryChunkIds: Ref<number[]> = ref([])
const loadedDetailChunkIds: Ref<number[]> = ref([])
const indexLoading: Ref<boolean> = ref(false)

async function initLoadedChunkIds() {
  const meta = await getMetadata(POEMS_STORAGE)
  if (meta) {
    loadedChunkIds.value = meta.loadedChunkIds
  }
  const summaryMeta = await getMetadata(POEMS_SUMMARY_STORAGE)
  if (summaryMeta) {
    loadedSummaryChunkIds.value = summaryMeta.loadedChunkIds
  }
  const detailMeta = await getMetadata(POEMS_DETAIL_STORAGE)
  if (detailMeta) {
    loadedDetailChunkIds.value = detailMeta.loadedChunkIds
  }
}
initLoadedChunkIds()

export function usePoemsV2() {
  const { metadata: poemsIndex, loading: indexLoading, error: indexError, loadMetadata } = usePoemsMetadata()

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
        genre: genre || '',
        chunk_id: chunkNum // 添加 chunk_id 用于快速定位
      })
    }

    poemSummaryCache.value.set(chunkNum, poems)
    await setChunkedCache(POEMS_SUMMARY_STORAGE, chunkNum, poems)

    if (!loadedChunkIds.value.includes(chunkNum)) {
      loadedChunkIds.value.push(chunkNum)
      await setMetadata(POEMS_STORAGE, { loadedChunkIds: [...loadedChunkIds.value], totalChunks: totalChunks.value })
    }

    // 为 poems-summary-v2 存储添加 metadata 以支持统计展示
    if (!loadedSummaryChunkIds.value.includes(chunkNum)) {
      loadedSummaryChunkIds.value.push(chunkNum)
      await setMetadata(POEMS_SUMMARY_STORAGE, {
        loadedChunkIds: [...loadedSummaryChunkIds.value],
        totalChunks: totalChunks.value
      })
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

    // 为 poems-detail-v2 存储添加 metadata 以支持统计展示
    if (!loadedDetailChunkIds.value.includes(chunkNum)) {
      loadedDetailChunkIds.value.push(chunkNum)
      await setMetadata(POEMS_DETAIL_STORAGE, {
        loadedChunkIds: [...loadedDetailChunkIds.value],
        totalChunks: totalChunks.value
      })
    }

    return poemMap
  }

  async function getPoemById(poemId: string, chunkId?: number): Promise<PoemDetail | null> {
    console.log(`[usePoemsV2] getPoemById START: ${poemId}, chunkId=${chunkId}`)
    const startTime = Date.now()

    // 1. 检查缓存
    for (const [chunkNum, chunkMap] of poemDetailCache.value.entries()) {
      if (chunkMap.has(poemId)) {
        console.log(`[usePoemsV2] Found in cache (chunk ${chunkNum}) in ${Date.now() - startTime}ms`)
        return chunkMap.get(poemId)!
      }
    }

    // 2. 如果提供了 chunk_id，直接加载该 chunk（快速路径）
    if (chunkId !== undefined) {
      console.log(`[usePoemsV2] Using fast path with chunkId ${chunkId}`)
      if (!poemDetailCache.value.has(chunkId)) {
        const loadStart = Date.now()
        const chunk = await loadChunkDetails(chunkId)
        console.log(`[usePoemsV2] Loaded chunk ${chunkId} in ${Date.now() - loadStart}ms`)
        poemDetailCache.value.set(chunkId, chunk)
      }
      const chunk = poemDetailCache.value.get(chunkId)
      if (chunk && chunk.has(poemId)) {
        console.log(`[usePoemsV2] Found in chunk ${chunkId} in ${Date.now() - startTime}ms`)
        return chunk.get(poemId)!
      }
      console.log(`[usePoemsV2] Not found in chunk ${chunkId}, falling back to full scan`)
      // 如果指定的 chunk 中没有，继续回退到全量搜索
    }

    // 3. 回退：顺序扫描所有 chunk（慢速路径）
    console.log(`[usePoemsV2] Using slow path: scanning all chunks`)
    const scanStart = Date.now()
    const index = await loadMetadata()

    for (const chunkInfo of index.chunks) {
      if (poemDetailCache.value.has(chunkInfo.id)) continue

      const chunk = await loadChunkDetails(chunkInfo.id)
      poemDetailCache.value.set(chunkInfo.id, chunk)

      if (chunk.has(poemId)) {
        console.log(`[usePoemsV2] Found in chunk ${chunkInfo.id} after scanning in ${Date.now() - scanStart}ms`)
        return chunk.get(poemId)!
      }
    }

    console.log(`[usePoemsV2] Poem ${poemId} not found after scanning all chunks in ${Date.now() - startTime}ms`)
    return null
  }

  /**
   * 批量获取诗词详情，使用 chunk_id 优化加载
   * 这个函数会先按 chunk_id 分组，然后并行加载所需的 chunks
   */
  async function getPoemsByIds(poemIds: string[], chunkIds?: number[]): Promise<PoemDetail[]> {
    console.log(`[usePoemsV2] getPoemsByIds START: ${poemIds.length} poems`)
    const startTime = Date.now()
    const results: PoemDetail[] = []
    const missingIds: string[] = []
    const missingChunkIds: (number | undefined)[] = []

    // 1. 先检查缓存
    const cacheCheckStart = Date.now()
    for (let i = 0; i < poemIds.length; i++) {
      const poemId = poemIds[i]
      if (poemId === undefined) continue
      let found = false

      for (const [chunkNum, chunkMap] of poemDetailCache.value.entries()) {
        if (chunkMap.has(poemId)) {
          results.push(chunkMap.get(poemId)!)
          found = true
          break
        }
      }

      if (!found) {
        missingIds.push(poemId)
        missingChunkIds.push(chunkIds?.[i])
      }
    }
    console.log(`[usePoemsV2] Cache check: ${results.length} cached, ${missingIds.length} missing in ${Date.now() - cacheCheckStart}ms`)

    if (missingIds.length === 0) {
      console.log(`[usePoemsV2] All poems in cache, returning ${results.length} poems`)
      return results
    }

    // 2. 按 chunk_id 分组，准备批量加载
    const chunksToLoad = new Map<number, string[]>()
    const idsWithoutChunk: string[] = []

    for (let i = 0; i < missingIds.length; i++) {
      const poemId = missingIds[i]
      if (poemId === undefined) continue
      const chunkId = missingChunkIds[i]

      if (chunkId !== undefined) {
        if (!chunksToLoad.has(chunkId)) {
          chunksToLoad.set(chunkId, [])
        }
        chunksToLoad.get(chunkId)!.push(poemId)
      } else {
        idsWithoutChunk.push(poemId)
      }
    }
    console.log(`[usePoemsV2] Grouped by chunk: ${chunksToLoad.size} chunks, ${idsWithoutChunk.length} without chunk_id`)

    // 3. 并行加载所有需要的 chunks
    const loadPromises: Promise<void>[] = []
    const loadStart = Date.now()

    for (const [chunkId, ids] of chunksToLoad.entries()) {
      if (poemDetailCache.value.has(chunkId)) {
        // chunk 已在缓存中，直接查找
        console.log(`[usePoemsV2] Chunk ${chunkId} already cached`)
        const chunk = poemDetailCache.value.get(chunkId)!
        for (const poemId of ids) {
          const poem = chunk.get(poemId)
          if (poem) {
            results.push(poem)
          }
        }
      } else {
        // 需要加载 chunk
        console.log(`[usePoemsV2] Loading chunk ${chunkId} with ${ids.length} poems`)
        loadPromises.push(
          loadChunkDetails(chunkId).then(chunk => {
            console.log(`[usePoemsV2] Chunk ${chunkId} loaded, size: ${chunk.size}`)
            poemDetailCache.value.set(chunkId, chunk)
            for (const poemId of ids) {
              const poem = chunk.get(poemId)
              if (poem) {
                results.push(poem)
              }
            }
          })
        )
      }
    }

    await Promise.all(loadPromises)
    console.log(`[usePoemsV2] All chunks loaded in ${Date.now() - loadStart}ms`)

    // 4. 处理没有 chunk_id 的诗词（回退到逐个查找）
    if (idsWithoutChunk.length > 0) {
      console.log(`[usePoemsV2] Loading ${idsWithoutChunk.length} poems without chunk_id individually`)
      const fallbackStart = Date.now()
      for (const poemId of idsWithoutChunk) {
        const poem = await getPoemById(poemId)
        if (poem) {
          results.push(poem)
        }
      }
      console.log(`[usePoemsV2] Fallback loading done in ${Date.now() - fallbackStart}ms`)
    }

    console.log(`[usePoemsV2] getPoemsByIds DONE: ${results.length} poems in ${Date.now() - startTime}ms`)
    return results
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
    poemCounts,
    indexLoading,
    loadMetadata,
    loadChunkSummaries,
    loadChunkDetails,
    getPoemById,
    getPoemsByIds,
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
