import { ref, shallowRef, computed, type Ref } from 'vue'

const KEYWORD_STORAGE = 'keyword-index'

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
  
  const stored = localStorage.getItem(`${KEYWORD_STORAGE}-meta`)
  if (stored) {
    const parsed = JSON.parse(stored)
    metadata.value = parsed
    loadedChunkIds.value = parsed.loadedChunkIds || []
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

    const chunkId = chunkIndex.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}../results/keyword_index/keyword_${chunkId}.json`)
    if (!response.ok) {
      console.warn(`Failed to load keyword chunk ${chunkIndex}`)
      return new Map()
    }

    const data: Record<string, string[]> = await response.json()
    const map = new Map(Object.entries(data))
    
    keywordCache.value.set(chunkIndex, map)

    if (!loadedChunkIds.value.includes(chunkIndex)) {
      loadedChunkIds.value.push(chunkIndex)
      const meta = await loadMetadata()
      meta.loadedChunkIds = [...loadedChunkIds.value]
      localStorage.setItem(`${KEYWORD_STORAGE}-meta`, JSON.stringify(meta))
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
