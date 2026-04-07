/**
 * 文件: web/src/composables/usePoems.ts
 * 说明: 管理诗词摘要与详情的分片加载、缓存、索引与暴露查询接口，支持 CSV 分片与 JSON 分片混合存储。
 *
 * 数据管线:
 *   - 元数据: 通过 `usePoemsMetadata` 获取分片数量、统计信息与索引映射（prefixMap）。
 *   - 摘要加载: `loadChunkSummaries` 读取 CSV 分片（preprocessed/poems_chunk_XXXX.csv），逐行解析并转换为 `PoemSummary`。
 *   - 详情加载: 通过 `getVerifiedChunk` 读取详情分片并缓存为 `PoemDetail`，并维护 `poemDetailCache` 以便按 id 查找。
 *   - 缓存验证: 使用 `getValidatedMetadata` 保持已加载分片的元数据一致性（版本校验）。
 *
 * 复杂度:
 *   - 读取单个摘要分片为 O(c)（c = 分片行数），遍历或拼接多分片为 O(t * c)。
 *   - 空间: 缓存已加载摘要/详情将使内存随已加载量线性增长 O(k)。
 *
 * 性能建议:
 *   - CSV 文本解析会分配大量字符串与数组，面对大型分片应考虑更紧凑的二进制格式或在 Worker 中解析。
 *   - 对于频繁按 id 访问详情，保持一个轻量索引（id -> chunk_id）可以减少重复网络请求。
 */
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
import { getMetadata, setMetadata, getChunkedCache, setChunkedCache, getValidatedMetadata } from './useCache'
import { getVerifiedChunk } from './useVerifiedCache'

// Separate storage keys for summaries and details to avoid cache conflicts
export const POEMS_SUMMARY_STORAGE = 'poems-summary-v2'
const POEMS_DETAIL_STORAGE = 'poems-detail-v2'

/** 存储版本号 */
const STORAGE_VERSION = 1

const poemSummaryCache = shallowRef<Map<number, PoemSummary[]>>(new Map())
const poemDetailCache = shallowRef<Map<number, Map<string, PoemDetail>>>(new Map())
const loadedChunkIds: Ref<number[]> = ref([])
const loadedSummaryChunkIds: Ref<number[]> = ref([])
const loadedDetailChunkIds: Ref<number[]> = ref([])
const indexLoading: Ref<boolean> = ref(false)

const loadingPromises = new Map<number, Promise<any>>()

async function initLoadedChunkIds() {
  // 使用版本验证获取元数据
  const meta = await getValidatedMetadata(POEMS_STORAGE, STORAGE_VERSION, { autoClean: true })
  if (meta) {
    loadedChunkIds.value = meta.loadedChunkIds
  } else {
    loadedChunkIds.value = []
  }

  const summaryMeta = await getValidatedMetadata(POEMS_SUMMARY_STORAGE, STORAGE_VERSION, { autoClean: true })
  if (summaryMeta) {
    loadedSummaryChunkIds.value = summaryMeta.loadedChunkIds
  } else {
    loadedSummaryChunkIds.value = []
  }

  const detailMeta = await getValidatedMetadata(POEMS_DETAIL_STORAGE, STORAGE_VERSION, { autoClean: true })
  if (detailMeta) {
    loadedDetailChunkIds.value = detailMeta.loadedChunkIds
  } else {
    loadedDetailChunkIds.value = []
  }
}
initLoadedChunkIds()

export function usePoems() {
  const { metadata: poemsIndex, loading: indexLoading, error: indexError, loadMetadata } = usePoemsMetadata()

  const totalPoems = computed(() => poemsIndex.value?.metadata?.total || 0)
  const totalChunks = computed(() => poemsIndex.value?.metadata?.chunks || 0)
  const dynasties = computed(() => poemsIndex.value?.stats?.dynasties || [])
  const genres = computed(() => poemsIndex.value?.stats?.genres || [])
  const poemCounts = computed(() => poemsIndex.value?.stats?.counts || { songshi: 0, songci: 0, tangshi: 0 })

  const loadedChunkCount = computed(() => loadedChunkIds.value.length)

  async function loadChunkSummaries(chunkNum: number): Promise<PoemSummary[]> {
    console.log(`[usePoems] loadChunkSummaries START: chunkNum=${chunkNum}`)
    
    // 如果已经有相同的加载请求在进行中，等待它完成
    if (loadingPromises.has(-chunkNum - 1)) {  // 用负数区分 summary 加载
      console.log(`[usePoems] loadChunkSummaries: chunk ${chunkNum} already loading, waiting...`)
      const existingPromise = loadingPromises.get(-chunkNum - 1)
      if (existingPromise) {
        await existingPromise
        const cached = poemSummaryCache.value.get(chunkNum)
        if (cached) {
          console.log(`[usePoems] loadChunkSummaries: chunk ${chunkNum} loaded by concurrent request`)
          return cached
        }
      }
    }
    
    if (poemSummaryCache.value.has(chunkNum)) {
      const cached = poemSummaryCache.value.get(chunkNum)!
      console.log(`[usePoems] loadChunkSummaries: chunk ${chunkNum} cache HIT, ${cached.length} poems`)
      return cached
    }

    // 创建并缓存加载 Promise，防止并发重复加载
    const loadPromise = (async () => {
      const chunkId = chunkNum.toString().padStart(4, '0')
      const filePath = `preprocessed/poems_chunk_${chunkId}.csv`

      const result = await getVerifiedChunk<PoemSummary[]>(
        POEMS_SUMMARY_STORAGE,
        chunkNum,
        filePath,
        async () => {
          const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
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
              chunk_id: chunkNum
            })
          }

          return poems
        }
      )

      if (!result.data) {
        throw new Error(`Failed to load chunk ${chunkNum}: ${result.error || 'Unknown error'}`)
      }

      console.log(`[usePoems] loadChunkSummaries: chunk ${chunkNum} loaded, ${result.data.length} poems`)

      poemSummaryCache.value.set(chunkNum, result.data)

      // Update metadata tracking
      if (!loadedChunkIds.value.includes(chunkNum)) {
        loadedChunkIds.value.push(chunkNum)
        await setMetadata(POEMS_STORAGE, {
          loadedChunkIds: [...loadedChunkIds.value],
          totalChunks: totalChunks.value,
          version: STORAGE_VERSION
        })
      }

      if (!loadedSummaryChunkIds.value.includes(chunkNum)) {
        loadedSummaryChunkIds.value.push(chunkNum)
        await setMetadata(POEMS_SUMMARY_STORAGE, {
          loadedChunkIds: [...loadedSummaryChunkIds.value],
          totalChunks: totalChunks.value,
          version: STORAGE_VERSION
        })
      }

      return result.data
    })()

    loadingPromises.set(-chunkNum - 1, loadPromise)
    
    try {
      return await loadPromise
    } finally {
      loadingPromises.delete(-chunkNum - 1)
    }
  }

  async function loadChunkDetails(chunkNum: number): Promise<Map<string, PoemDetail>> {
    console.log(`[usePoems] loadChunkDetails START: chunk ${chunkNum}`)
    
    // 如果已经有相同的加载请求在进行中，等待它完成
    if (loadingPromises.has(chunkNum)) {
      console.log(`[usePoems] loadChunkDetails: chunk ${chunkNum} already loading, waiting...`)
      const existingPromise = loadingPromises.get(chunkNum)
      if (existingPromise) {
        await existingPromise
        const cached = poemDetailCache.value.get(chunkNum)
        if (cached) {
          console.log(`[usePoems] loadChunkDetails: chunk ${chunkNum} loaded by concurrent request`)
          return cached
        }
      }
    }
    
    // 检查缓存
    if (poemDetailCache.value.has(chunkNum)) {
      console.log(`[usePoems] loadChunkDetails: chunk ${chunkNum} already in cache`)
      return poemDetailCache.value.get(chunkNum)!
    }

    // 创建并缓存加载 Promise，防止并发重复加载
    const loadPromise = (async () => {
      const chunkId = chunkNum.toString().padStart(4, '0')
      const filePath = `preprocessed/poems_chunk_${chunkId}.csv`
      console.log(`[usePoems] loadChunkDetails: loading from ${filePath}`)

      const result = await getVerifiedChunk<Record<string, PoemDetail>>(
        POEMS_DETAIL_STORAGE,
        chunkNum,
        filePath,
        async () => {
          console.log(`[usePoems] loadChunkDetails: fetching ${filePath}`)
          const fetchStart = Date.now()
          const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
          console.log(`[usePoems] loadChunkDetails: fetch response ${response.status} in ${Date.now() - fetchStart}ms`)
          if (!response.ok) throw new Error(`Failed to load chunk ${chunkNum}`)

          const parseStart = Date.now()
          const csvText = await response.text()
          const lines = csvText.trim().split('\n')
          const dataLines = lines.slice(1)
          console.log(`[usePoems] loadChunkDetails: parsed ${dataLines.length} lines in ${Date.now() - parseStart}ms`)

          const poemRecord: Record<string, PoemDetail> = {}

          for (const line of dataLines) {
            const cols = parseCsvLine(line)
            if (cols.length < 10) continue

            const [id, title, author, dynasty, genre, poemType, sentences, meterPattern, hash, words] = cols
            const poemId = id || ''

            poemRecord[poemId] = {
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
            }
          }
          console.log(`[usePoems] loadChunkDetails: processed ${Object.keys(poemRecord).length} poems`)

          return poemRecord
        }
      )

      if (!result.data) {
        throw new Error(`Failed to load chunk ${chunkNum}: ${result.error || 'Unknown error'}`)
      }

      const poemMap = new Map<string, PoemDetail>(Object.entries(result.data))
      poemDetailCache.value.set(chunkNum, poemMap)
      console.log(`[usePoems] loadChunkDetails: cached chunk ${chunkNum}, map size: ${poemMap.size}`)

      // Update metadata tracking
      if (!loadedDetailChunkIds.value.includes(chunkNum)) {
        loadedDetailChunkIds.value.push(chunkNum)
        await setMetadata(POEMS_DETAIL_STORAGE, {
          loadedChunkIds: [...loadedDetailChunkIds.value],
          totalChunks: totalChunks.value,
          version: STORAGE_VERSION
        })
      }

      console.log(`[usePoems] loadChunkDetails END: chunk ${chunkNum}`)
      return poemMap
    })()

    loadingPromises.set(chunkNum, loadPromise)
    
    try {
      return await loadPromise
    } finally {
      loadingPromises.delete(chunkNum)
    }
  }

  async function getPoemById(poemId: string, chunkId?: number): Promise<PoemDetail | null> {
    console.log(`[usePoems] getPoemById START: ${poemId}, chunkId=${chunkId}`)
    const startTime = Date.now()

    // 1. 检查缓存
    for (const [chunkNum, chunkMap] of poemDetailCache.value.entries()) {
      if (chunkMap.has(poemId)) {
        console.log(`[usePoems] Found in cache (chunk ${chunkNum}) in ${Date.now() - startTime}ms`)
        return chunkMap.get(poemId)!
      }
    }

    // 2. 如果提供了 chunk_id，直接加载该 chunk（快速路径）
    if (chunkId !== undefined) {
      console.log(`[usePoems] Using fast path with chunkId ${chunkId}`)
      if (!poemDetailCache.value.has(chunkId)) {
        const loadStart = Date.now()
        const chunk = await loadChunkDetails(chunkId)
        console.log(`[usePoems] Loaded chunk ${chunkId} in ${Date.now() - loadStart}ms`)
        poemDetailCache.value.set(chunkId, chunk)
      }
      const chunk = poemDetailCache.value.get(chunkId)
      if (chunk && chunk.has(poemId)) {
        console.log(`[usePoems] Found in chunk ${chunkId} in ${Date.now() - startTime}ms`)
        return chunk.get(poemId)!
      }
      console.log(`[usePoems] Not found in chunk ${chunkId}, falling back to full scan`)
      // 如果指定的 chunk 中没有，继续回退到全量搜索
    }

    // 3. 回退：顺序扫描所有 chunk（慢速路径）
    console.log(`[usePoems] Using slow path: scanning all chunks`)
    const scanStart = Date.now()
    const index = await loadMetadata()

    for (const chunkInfo of index.chunks) {
      if (poemDetailCache.value.has(chunkInfo.id)) continue

      const chunk = await loadChunkDetails(chunkInfo.id)
      poemDetailCache.value.set(chunkInfo.id, chunk)

      if (chunk.has(poemId)) {
        console.log(`[usePoems] Found in chunk ${chunkInfo.id} after scanning in ${Date.now() - scanStart}ms`)
        return chunk.get(poemId)!
      }
    }

    console.log(`[usePoems] Poem ${poemId} not found after scanning all chunks in ${Date.now() - startTime}ms`)
    return null
  }

  /**
   * 批量获取诗词详情，使用 chunk_id 优化加载
   * 这个函数会先按 chunk_id 分组，然后并行加载所需的 chunks
   */
  async function getPoemsByIds(poemIds: string[], chunkIds?: number[]): Promise<PoemDetail[]> {
    console.log(`[usePoems] getPoemsByIds START: ${poemIds.length} poems`)
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
    console.log(`[usePoems] Cache check: ${results.length} cached, ${missingIds.length} missing in ${Date.now() - cacheCheckStart}ms`)

    if (missingIds.length === 0) {
      console.log(`[usePoems] All poems in cache, returning ${results.length} poems`)
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
    console.log(`[usePoems] Grouped by chunk: ${chunksToLoad.size} chunks, ${idsWithoutChunk.length} without chunk_id`)

    // 3. 并行加载所有需要的 chunks
    const loadPromises: Promise<void>[] = []
    const loadStart = Date.now()

    for (const [chunkId, ids] of chunksToLoad.entries()) {
      if (poemDetailCache.value.has(chunkId)) {
        // chunk 已在缓存中，直接查找
        console.log(`[usePoems] Chunk ${chunkId} already cached`)
        const chunk = poemDetailCache.value.get(chunkId)!
        for (const poemId of ids) {
          const poem = chunk.get(poemId)
          if (poem) {
            results.push(poem)
          }
        }
      } else {
        // 需要加载 chunk
        console.log(`[usePoems] Loading chunk ${chunkId} with ${ids.length} poems`)
        loadPromises.push(
          loadChunkDetails(chunkId).then(chunk => {
            console.log(`[usePoems] Chunk ${chunkId} loaded, size: ${chunk.size}`)
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
    console.log(`[usePoems] All chunks loaded in ${Date.now() - loadStart}ms`)

    // 4. 处理没有 chunk_id 的诗词（回退到逐个查找）
    if (idsWithoutChunk.length > 0) {
      console.log(`[usePoems] Loading ${idsWithoutChunk.length} poems without chunk_id individually`)
      const fallbackStart = Date.now()
      for (const poemId of idsWithoutChunk) {
        const poem = await getPoemById(poemId)
        if (poem) {
          results.push(poem)
        }
      }
      console.log(`[usePoems] Fallback loading done in ${Date.now() - fallbackStart}ms`)
    }

    console.log(`[usePoems] getPoemsByIds DONE: ${results.length} poems in ${Date.now() - startTime}ms`)
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
    console.log(`[usePoems] queryPoems START: page=${page}, pageSize=${pageSize}, filter=`, filter)
    const index = await loadMetadata()
    const relevantChunks = getRelevantChunks(filter)
    console.log(`[usePoems] queryPoems: relevantChunks=${relevantChunks.length} chunks, ids=[${relevantChunks.slice(0, 10).join(',')}${relevantChunks.length > 10 ? '...' : ''}]`)

    // 计算总符合条件的诗词数量（用于分页）
    let totalFilteredPoems = 0
    for (const chunkId of relevantChunks) {
      const chunkInfo = poemsIndex.value?.chunks.find(c => c.id === chunkId)
      if (chunkInfo) {
        totalFilteredPoems += chunkInfo.count
      }
    }
    console.log(`[usePoems] queryPoems: totalFilteredPoems=${totalFilteredPoems}`)

    const poemsPerChunk = 1000
    const startIndex = (page - 1) * pageSize
    const endIndex = startIndex + pageSize

    // 计算需要加载的 chunks
    // 策略：遍历相关 chunks，累积计数，找到包含目标范围的 chunks
    let accumulatedCount = 0
    const chunksToLoad: number[] = []
    let skipCount = 0 // 需要跳过的诗词数量（在当前 chunk 内）
    let takeCount = pageSize // 需要获取的诗词数量

    for (const chunkId of relevantChunks) {
      const chunkInfo = poemsIndex.value?.chunks.find(c => c.id === chunkId)
      if (!chunkInfo) continue

      const chunkStart = accumulatedCount
      const chunkEnd = accumulatedCount + chunkInfo.count

      // 检查这个 chunk 是否包含目标范围
      if (chunkEnd > startIndex && chunkStart < endIndex) {
        chunksToLoad.push(chunkId)
        
        // 如果是第一个需要加载的 chunk，计算需要跳过多少
        if (chunksToLoad.length === 1) {
          skipCount = Math.max(0, startIndex - chunkStart)
        }
      }

      accumulatedCount += chunkInfo.count
      
      // 如果已经收集够数据，提前退出
      if (accumulatedCount >= endIndex && chunksToLoad.length > 0) {
        break
      }
    }

    console.log(`[usePoems] queryPoems: chunksToLoad=[${chunksToLoad.join(',')}], skipCount=${skipCount}`)
    
    const allPoems: PoemSummary[] = []

    for (const chunkId of chunksToLoad) {
      const chunkPoems = await loadChunkSummaries(chunkId)
      console.log(`[usePoems] queryPoems: chunk ${chunkId} returned ${chunkPoems.length} poems`)
      allPoems.push(...chunkPoems)
    }

    console.log(`[usePoems] queryPoems: allPoems.length=${allPoems.length}`)

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

    // 在加载的 poems 中，跳过前面的，取需要的数量
    const paged = filtered.slice(skipCount, skipCount + pageSize)
    console.log(`[usePoems] queryPoems: paged.length=${paged.length}, skipCount=${skipCount}, pageSize=${pageSize}`)

    // 计算过滤后的总数
    const filteredTotal = filter?.author 
      ? totalFilteredPoems // 如果有作者过滤，需要实际计算，这里简化处理
      : totalFilteredPoems

    return {
      poems: paged,
      total: index.metadata.total,
      filteredTotal: filteredTotal,
      page,
      pageSize,
      hasMore: endIndex < filteredTotal
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
