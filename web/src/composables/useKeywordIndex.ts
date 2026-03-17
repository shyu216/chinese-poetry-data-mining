import { ref, shallowRef, computed, type Ref } from 'vue'

const KEYWORD_INDEX_STORAGE = 'keyword-index-v2'

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
  
  const { getCache, getMetadata } = await import('./useCacheV2')
  
  const storedMeta = await getMetadata(KEYWORD_INDEX_STORAGE)
  if (storedMeta?.loadedChunkIds) {
    metadata.value = {
      total_chunks: storedMeta.totalChunks || 201,
      loadedChunkIds: storedMeta.loadedChunkIds || []
    }
    loadedChunkIds.value = storedMeta.loadedChunkIds || []
    isMetaInitialized.value = true
    return metadata.value
  }
  
  metadata.value = {
    total_chunks: 201,
    loadedChunkIds: []
  }
  isMetaInitialized.value = true
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
    
    const targetChunk = Math.floor(hashKeyword(keyword) % (metadata.value?.total_chunks || 201))
    
    const chunkMap = await loadChunk(targetChunk)
    return chunkMap.get(keyword) || []
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

function hashKeyword(keyword: string): number {
  let hash = 0
  for (let i = 0; i < keyword.length; i++) {
    const char = keyword.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash)
}
