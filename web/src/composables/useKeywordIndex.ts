import { ref, shallowRef, computed, type Ref } from 'vue'
import { KEYWORD_INDEX_STORAGE } from './useMetadataLoader'

interface KeywordIndexMeta {
  total_chunks: number
  loadedChunkIds: number[]
}

const keywordCache = shallowRef<Map<number, Map<string, string[]>>>(new Map())
const loadedChunkIds: Ref<number[]> = ref([])
const metadata = ref<KeywordIndexMeta>({
  total_chunks: 0,
  loadedChunkIds: []
})
const isMetaInitialized = ref(false)
const loading = ref(false)

async function loadMetadata(): Promise<KeywordIndexMeta> {
  if (isMetaInitialized.value) return metadata.value
  
  const { getCache, getMetadata, setMetadata: setCacheMetadata } = await import('./useCacheV2')
  
  // 首先尝试从服务器获取真实的 metadata
  try {
    const response = await fetch(`${import.meta.env.BASE_URL}data/keyword_index/metadata.json`)
    if (response.ok) {
      const serverMeta = await response.json()
      if (serverMeta?.statistics?.index_chunks) {
        metadata.value = {
          total_chunks: serverMeta.statistics.index_chunks,
          loadedChunkIds: []
        }
        // 缓存到 IndexedDB
        await setCacheMetadata(KEYWORD_INDEX_STORAGE, {
          totalChunks: serverMeta.statistics.index_chunks,
          loadedChunkIds: []
        })
        isMetaInitialized.value = true
        console.log(`[KeywordIndex] Loaded metadata from server: ${serverMeta.statistics.index_chunks} chunks`)
        return metadata.value
      }
    }
  } catch (e) {
    console.warn('[KeywordIndex] Failed to load metadata from server:', e)
  }
  
  // 回退到本地缓存
  const storedMeta = await getMetadata(KEYWORD_INDEX_STORAGE)
  if (storedMeta?.totalChunks) {
    metadata.value = {
      total_chunks: storedMeta.totalChunks,
      loadedChunkIds: storedMeta.loadedChunkIds || []
    }
    loadedChunkIds.value = storedMeta.loadedChunkIds || []
    isMetaInitialized.value = true
    console.log(`[KeywordIndex] Loaded metadata from cache: ${storedMeta.totalChunks} chunks`)
    return metadata.value
  }
  
  // 最后的默认值
  metadata.value = {
    total_chunks: 894, // 根据实际数据更新
    loadedChunkIds: []
  }
  isMetaInitialized.value = true
  console.warn('[KeywordIndex] Using default metadata: 894 chunks')
  return metadata.value
}

export function useKeywordIndex() {
  const totalChunks = computed(() => metadata.value?.total_chunks || 201)

  async function loadChunk(chunkIndex: number): Promise<Map<string, string[]>> {
    if (keywordCache.value.has(chunkIndex)) {
      return keywordCache.value.get(chunkIndex)!
    }

    const { getChunkedCache, setChunkedCache, setMetadata } = await import('./useCacheV2')
    
    const cached = await getChunkedCache<Record<string, string[]>>(KEYWORD_INDEX_STORAGE, chunkIndex)
    if (cached) {
      const map = new Map(Object.entries(cached))
      keywordCache.value.set(chunkIndex, map)
      if (!loadedChunkIds.value.includes(chunkIndex)) {
        loadedChunkIds.value.push(chunkIndex)
      }
      return map
    }

    const chunkId = chunkIndex.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}data/keyword_index/keyword_${chunkId}.json`)
    if (!response.ok) {
      console.warn(`Failed to load keyword chunk ${chunkIndex}`)
      return new Map()
    }

    const data: Record<string, string[]> = await response.json()
    const map = new Map(Object.entries(data))
    
    keywordCache.value.set(chunkIndex, map)
    
    await setChunkedCache(KEYWORD_INDEX_STORAGE, chunkIndex, data)

    if (!loadedChunkIds.value.includes(chunkIndex)) {
      loadedChunkIds.value.push(chunkIndex)
      await setMetadata(KEYWORD_INDEX_STORAGE, {
        loadedChunkIds: [...loadedChunkIds.value],
        totalChunks: metadata.value.total_chunks
      })
    }

    return map
  }

  async function searchKeyword(keyword: string): Promise<string[]> {
    await loadMetadata()
    
    // 首先检查已加载的 chunk
    for (const chunkIndex of loadedChunkIds.value) {
      const chunkMap = keywordCache.value.get(chunkIndex)
      if (chunkMap && chunkMap.has(keyword)) {
        return chunkMap.get(keyword) || []
      }
    }
    
    // 遍历所有 chunk 查找关键词
    // 注意：后端是按字母顺序分块，不是哈希分桶
    const totalChunks = metadata.value?.total_chunks || 894
    for (let i = 0; i < totalChunks; i++) {
      // 跳过已检查的 chunk
      if (loadedChunkIds.value.includes(i)) continue
      
      const chunkMap = await loadChunk(i)
      if (chunkMap.has(keyword)) {
        console.log(`[KeywordIndex] Found keyword "${keyword}" in chunk ${i}`)
        return chunkMap.get(keyword) || []
      }
    }
    
    console.warn(`[KeywordIndex] Keyword "${keyword}" not found in any chunk`)
    return []
  }

  async function getKeywordPoemIds(keyword: string): Promise<string[]> {
    return searchKeyword(keyword)
  }

  return {
    loadMetadata,
    loadChunk,
    searchKeyword,
    getKeywordPoemIds,
    totalChunks,
    loadedChunkIds: computed(() => loadedChunkIds.value),
    storageName: KEYWORD_INDEX_STORAGE,
    loading: computed(() => loading.value)
  }
}


