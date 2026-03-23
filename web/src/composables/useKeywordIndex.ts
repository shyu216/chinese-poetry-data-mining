import { ref, shallowRef, computed, type Ref } from 'vue'
import { WORDCOUNT_STORAGE } from './useMetadataLoader'
import { getVerifiedCache } from './useVerifiedCache'
import { getMetadata, setMetadata, getValidatedMetadata } from './useCacheV2'

interface KeywordManifest {
  version: string
  timestamp: string
  statistics: {
    total_keywords: number
    total_chunks: number
  }
  keywordToChunk: Record<string, number>
}

interface KeywordIndexMeta {
  total_chunks: number
  loadedChunkIds: number[]
}

/** 存储版本号 */
const STORAGE_VERSION = 1

// 内存缓存
const keywordCache = shallowRef<Map<number, Map<string, string[]>>>(new Map())
const loadedChunkIds: Ref<number[]> = ref([])
const keywordManifest = shallowRef<KeywordManifest | null>(null)
const isManifestLoaded = ref(false)

// 初始化：从 IndexedDB 恢复已加载的 chunk IDs
async function initLoadedChunkIds() {
  const meta = await getValidatedMetadata(WORDCOUNT_STORAGE, STORAGE_VERSION, { autoClean: true })
  if (meta?.loadedChunkIds) {
    loadedChunkIds.value = meta.loadedChunkIds
    console.log(`[KeywordIndex] Restored ${loadedChunkIds.value.length} loaded chunks from cache`)
  } else {
    loadedChunkIds.value = []
  }
}
initLoadedChunkIds()

/**
 * 加载关键词 Manifest（O(1) 查询所需）
 * 借鉴 useWordcountV2 和 useVerifiedCache 的模式
 */
async function loadKeywordManifest(): Promise<KeywordManifest | null> {
  if (isManifestLoaded.value) return keywordManifest.value

  const startTime = performance.now()

  // 使用 getVerifiedCache 进行 hash 验证的缓存加载
  const result = await getVerifiedCache<KeywordManifest>(
    WORDCOUNT_STORAGE,
    'keyword_manifest',
    'wordcount_v2/keyword_manifest.json',
    async () => {
      const response = await fetch(`${import.meta.env.BASE_URL}data/wordcount_v2/keyword_manifest.json`)
      if (!response.ok) {
        console.warn('[KeywordIndex] Manifest not found, falling back to linear search')
        return null
      }
      return response.json()
    }
  )

  if (result.data) {
    keywordManifest.value = result.data
    isManifestLoaded.value = true
    const duration = Math.round(performance.now() - startTime)
    console.log(`[KeywordIndex] Loaded manifest: ${result.data.statistics.total_keywords.toLocaleString()} keywords, ${result.data.statistics.total_chunks} chunks in ${duration}ms`)
    console.log(`[KeywordIndex] Cache status: fromCache=${result.fromCache}, hashMatch=${result.hashMatch}`)
    return result.data
  }

  isManifestLoaded.value = true
  console.warn('[KeywordIndex] Manifest not available, will use linear search (O(N))')
  return null
}

export function useKeywordIndex() {
  const totalChunks = computed(() => keywordManifest.value?.statistics?.total_chunks || 894)

  async function loadChunk(chunkIndex: number): Promise<Map<string, string[]>> {
    // 1. 检查内存缓存
    if (keywordCache.value.has(chunkIndex)) {
      return keywordCache.value.get(chunkIndex)!
    }

    const chunkId = chunkIndex.toString().padStart(4, '0')
    const filePath = `keyword_index/keyword_${chunkId}.json`

    // 2. 使用 getVerifiedChunk 进行 hash 验证的缓存加载
    const { getVerifiedChunk } = await import('./useVerifiedCache')
    const result = await getVerifiedChunk<Record<string, string[]>>(
      WORDCOUNT_STORAGE,
      chunkIndex,
      filePath,
      async () => {
        const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
        if (!response.ok) {
          throw new Error(`Failed to load keyword chunk ${chunkIndex}`)
        }
        return response.json()
      }
    )

    if (!result.data) {
      console.error(`[KeywordIndex] Failed to load chunk ${chunkIndex}:`, {
        error: result.error || 'Data is null',
        valid: result.valid,
        fromCache: result.fromCache,
        hashMatch: result.hashMatch
      })
      return new Map()
    }

    // 3. 转换为 Map 并缓存到内存
    const map = new Map(Object.entries(result.data))
    keywordCache.value.set(chunkIndex, map)

    // 4. 更新已加载 chunk IDs 并持久化到 IndexedDB
    if (!loadedChunkIds.value.includes(chunkIndex)) {
      loadedChunkIds.value.push(chunkIndex)
      await setMetadata(WORDCOUNT_STORAGE, {
        loadedChunkIds: [...loadedChunkIds.value],
        totalChunks: totalChunks.value,
        version: STORAGE_VERSION
      })
    }

    return map
  }

  /**
   * O(1) 查询关键词所在的 chunk
   * 借鉴 useSearchIndexV2 的批量加载模式
   */
  async function searchKeywordOptimized(keyword: string): Promise<string[]> {
    const startTime = performance.now()

    // 1. 首先检查内存缓存（已加载的 chunks）
    for (const chunkIndex of loadedChunkIds.value) {
      const chunkMap = keywordCache.value.get(chunkIndex)
      if (chunkMap && chunkMap.has(keyword)) {
        const poemIds = chunkMap.get(keyword) || []
        const duration = Math.round(performance.now() - startTime)
        console.log(`[KeywordIndex] O(1) Memory cache hit: "${keyword}" in chunk ${chunkIndex}, ${poemIds.length} poems, ${duration}ms`)
        return poemIds
      }
    }

    // 2. 加载 manifest（如果还没加载）
    const manifest = await loadKeywordManifest()

    if (manifest?.keywordToChunk) {
      // O(1) 直接查找 chunk_id
      const chunkId = manifest.keywordToChunk[keyword]

      if (chunkId !== undefined) {
        console.log(`[KeywordIndex] O(1) Manifest hit: "${keyword}" -> chunk ${chunkId}`)
        const chunkMap = await loadChunk(chunkId)
        const poemIds = chunkMap.get(keyword) || []
        const duration = Math.round(performance.now() - startTime)
        console.log(`[KeywordIndex] O(1) Loaded "${keyword}": ${poemIds.length} poems in ${duration}ms`)
        return poemIds
      } else {
        console.log(`[KeywordIndex] O(1) Keyword "${keyword}" not found in manifest`)
        return []
      }
    }

    // 3. 回退到线性搜索（O(N)）
    console.warn(`[KeywordIndex] Falling back to linear search for "${keyword}"`)
    return searchKeywordLinear(keyword)
  }

  /**
   * 线性搜索（O(N)）- 作为后备方案
   * 当 manifest 不可用时使用
   */
  async function searchKeywordLinear(
    keyword: string,
    onProgress?: (currentChunk: number, totalChunks: number, found: boolean) => void
  ): Promise<string[]> {
    const total = totalChunks.value

    // 首先检查已加载的 chunk
    for (const chunkIndex of loadedChunkIds.value) {
      const chunkMap = keywordCache.value.get(chunkIndex)
      if (chunkMap && chunkMap.has(keyword)) {
        return chunkMap.get(keyword) || []
      }
    }

    // 遍历所有 chunk 查找关键词
    for (let i = 0; i < total; i++) {
      // 跳过已检查的 chunk
      if (loadedChunkIds.value.includes(i)) continue

      // 报告进度
      if (onProgress) {
        onProgress(i + 1, total, false)
      }

      const chunkMap = await loadChunk(i)
      if (chunkMap.has(keyword)) {
        console.log(`[KeywordIndex] Linear search found "${keyword}" in chunk ${i}`)
        if (onProgress) {
          onProgress(i + 1, total, true)
        }
        return chunkMap.get(keyword) || []
      }
    }

    console.warn(`[KeywordIndex] Keyword "${keyword}" not found in any chunk`)
    return []
  }

  /**
   * 通用搜索接口
   * 默认使用 O(1) 优化查询，支持进度回调时回退到线性搜索
   */
  async function searchKeyword(
    keyword: string,
    onProgress?: (currentChunk: number, totalChunks: number, found: boolean) => void
  ): Promise<string[]> {
    // 如果提供了 onProgress 回调，说明需要进度报告，使用线性搜索
    if (onProgress) {
      return searchKeywordLinear(keyword, onProgress)
    }
    return searchKeywordOptimized(keyword)
  }

  /**
   * 获取关键词对应的诗词 IDs（O(1) 优化版本）
   */
  async function getKeywordPoemIds(keyword: string): Promise<string[]> {
    return searchKeywordOptimized(keyword)
  }

  /**
   * 预加载指定 chunk 范围（用于优化批量查询）
   * 借鉴 useWordcountV2 的 preloadChunks 模式
   */
  async function preloadChunks(startChunk: number, endChunk: number): Promise<void> {
    const chunksToLoad = []
    for (let i = startChunk; i <= endChunk && i < totalChunks.value; i++) {
      if (!loadedChunkIds.value.includes(i)) {
        chunksToLoad.push(loadChunk(i))
      }
    }
    await Promise.all(chunksToLoad)
    console.log(`[KeywordIndex] Preloaded chunks ${startChunk}-${endChunk}`)
  }

  /**
   * 清除缓存
   */
  async function clearCache(): Promise<void> {
    keywordCache.value.clear()
    loadedChunkIds.value = []
    keywordManifest.value = null
    isManifestLoaded.value = false
    await setMetadata(WORDCOUNT_STORAGE, {
      loadedChunkIds: [],
      totalChunks: 0
    })
    console.log('[KeywordIndex] Cache cleared')
  }

  return {
    // 核心方法
    searchKeyword,
    searchKeywordOptimized,
    searchKeywordLinear,
    getKeywordPoemIds,
    loadChunk,
    preloadChunks,
    clearCache,

    // 状态
    totalChunks,
    loadedChunkIds: computed(() => loadedChunkIds.value),
    isManifestLoaded: computed(() => isManifestLoaded.value),
    manifestStats: computed(() => keywordManifest.value?.statistics || null),
    manifestVersion: computed(() => keywordManifest.value?.version || null),

    // 存储名称（用于外部访问）
    storageName: WORDCOUNT_STORAGE
  }
}
