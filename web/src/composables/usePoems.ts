import { ref, shallowRef } from 'vue'
import {
  cacheChunkSummaries,
  cacheChunkDetails,
  cacheIndex,
  cacheMetadata,
  getCachedChunkSummaries,
  getCachedChunkDetails,
  getCachedIndex,
  getCachedMetadata
} from './usePoemCache'

export interface PoemSummary {
  id: string
  title: string
  author: string
  dynasty: string
  genre: string
}

export interface PoemDetail extends PoemSummary {
  poem_type?: string
  meter_pattern?: string
  sentences: string[]
  words: string[]
  hash: string
}

interface ChunkInfo {
  id: number
  file: string
  count: number
  dynasties: string[]
  genres: string[]
}

interface IndexData {
  metadata: { total: number; chunks: number }
  stats: { dynasties: string[]; genres: string[] }
  chunks: ChunkInfo[]
}

const indexCache = shallowRef<IndexData | null>(null)
const chunkCache = shallowRef<Map<number, PoemSummary[]>>(new Map())
const loading = ref(false)
const loadingChunk = ref(false)
const error = ref<string | null>(null)

// Track loaded chunk IDs for persistence
let loadedChunkIds: number[] = []

// Parse CSV line handling quoted fields
function parseCSVLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  result.push(current.trim())
  return result
}

export function usePoems() {
  const loadIndex = async (): Promise<IndexData> => {
    if (indexCache.value) return indexCache.value

    // Try to get from IndexedDB cache first
    const cached = await getCachedIndex()
    if (cached) {
      indexCache.value = cached
      return cached
    }

    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/index.json`)
      if (!response.ok) throw new Error('Failed to load index')
      const data: IndexData = await response.json()
      indexCache.value = data
      // Cache to IndexedDB
      await cacheIndex(data)
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      throw e
    } finally {
      loading.value = false
    }
  }

  const loadChunkSummaries = async (chunkNum: number): Promise<PoemSummary[]> => {
    if (chunkCache.value.has(chunkNum)) {
      return chunkCache.value.get(chunkNum)!
    }

    // Try to get from IndexedDB cache first
    const cached = await getCachedChunkSummaries(chunkNum)
    if (cached) {
      chunkCache.value.set(chunkNum, cached)
      return cached
    }

    loadingChunk.value = true
    try {
      const chunkId = chunkNum.toString().padStart(4, '0')
      const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/poems_chunk_${chunkId}.csv`)
      if (!response.ok) throw new Error(`Failed to load chunk ${chunkNum}`)
      
      const csvText = await response.text()
      const lines = csvText.trim().split('\n')
      
      // Skip header
      const dataLines = lines.slice(1)
      
      const poems: PoemSummary[] = []
      
      for (const line of dataLines) {
        const cols = parseCSVLine(line)
        if (cols.length < 10) continue
        
        const [id, title, author, dynasty, genre] = cols
        
        poems.push({
          id: id || '',
          title: title || '',
          author: author || '佚名',
          dynasty: dynasty || '',
          genre: genre || ''
        })
      }
      
      chunkCache.value.set(chunkNum, poems)
      // Cache to IndexedDB
      await cacheChunkSummaries(chunkNum, poems)
      // Track loaded chunk ID
      if (!loadedChunkIds.includes(chunkNum)) {
        loadedChunkIds.push(chunkNum)
        await cacheMetadata(loadedChunkIds)
      }
      return poems
    } catch (e) {
      console.error(`Error loading chunk ${chunkNum}:`, e)
      return []
    } finally {
      loadingChunk.value = false
    }
  }

  const loadChunkDetails = async (chunkNum: number): Promise<Map<string, PoemDetail>> => {
    const chunkId = chunkNum.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/poems_chunk_${chunkId}.csv`)
    if (!response.ok) throw new Error(`Failed to load chunk ${chunkNum}`)

    const csvText = await response.text()
    const lines = csvText.trim().split('\n')
    const dataLines = lines.slice(1)

    const poemMap = new Map<string, PoemDetail>()
    
    for (const line of dataLines) {
      const cols = parseCSVLine(line)
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
    
    return poemMap
  }

  // Cache for chunk details
  const chunkDetailCache = shallowRef<Map<number, Map<string, PoemDetail>>>(new Map())

  const getPoemDetail = async (id: string): Promise<PoemDetail | null> => {
    // First check if poem is in any already loaded chunk
    for (const [chunkNum, chunkMap] of chunkDetailCache.value.entries()) {
      if (chunkMap.has(id)) {
        return chunkMap.get(id)!
      }
    }
    
    // Load index to find which chunk contains this poem
    const index = await loadIndex()
    
    // Search through chunks to find the poem
    // Try already loaded summary chunks first
    for (const chunkNum of chunkCache.value.keys()) {
      if (!chunkDetailCache.value.has(chunkNum)) {
        const chunk = await loadChunkDetails(chunkNum)
        chunkDetailCache.value.set(chunkNum, chunk)
        if (chunk.has(id)) {
          return chunk.get(id)!
        }
      }
    }
    
    // If not found, search through all chunks
    for (const chunkInfo of index.chunks) {
      if (chunkDetailCache.value.has(chunkInfo.id)) continue
      
      const chunk = await loadChunkDetails(chunkInfo.id)
      chunkDetailCache.value.set(chunkInfo.id, chunk)
      
      if (chunk.has(id)) {
        return chunk.get(id)!
      }
    }
    
    return null
  }

  // Get relevant chunk IDs based on filters
  const getRelevantChunks = (index: IndexData, filters?: { dynasty?: string; genre?: string }): number[] => {
    return index.chunks
      .filter(chunk => {
        if (filters?.dynasty && !chunk.dynasties.includes(filters.dynasty)) {
          return false
        }
        if (filters?.genre && !chunk.genres.includes(filters.genre)) {
          return false
        }
        return true
      })
      .map(chunk => chunk.id)
  }

  const getAllPoems = async (
    filters?: { dynasty?: string; genre?: string; search?: string },
    page: number = 1,
    pageSize: number = 24
  ): Promise<{ poems: PoemSummary[]; total: number; filteredTotal: number }> => {
    const index = await loadIndex()
    
    // Get chunks that match the filters
    const relevantChunkIds = getRelevantChunks(index, {
      dynasty: filters?.dynasty,
      genre: filters?.genre
    })
    
    // Calculate which chunks to load based on page
    const poemsPerChunk = 1000 // Approximate
    const startPoemIndex = (page - 1) * pageSize
    const endPoemIndex = startPoemIndex + pageSize - 1
    
    const startChunkIndex = Math.floor(startPoemIndex / poemsPerChunk)
    const endChunkIndex = Math.floor(endPoemIndex / poemsPerChunk)
    
    // Load current chunks
    const chunksToLoad = relevantChunkIds.slice(startChunkIndex, endChunkIndex + 1)
    const allPoems: PoemSummary[] = []
    
    for (const chunkId of chunksToLoad) {
      const chunkPoems = await loadChunkSummaries(chunkId)
      allPoems.push(...chunkPoems)
    }
    
    // Preload next chunk if exists and we're near the end
    const nextChunkIndex = endChunkIndex + 1
    if (nextChunkIndex < relevantChunkIds.length) {
      const nextChunkId = relevantChunkIds[nextChunkIndex]
      if (nextChunkId !== undefined) {
        // Preload in background without awaiting
        setTimeout(() => {
          loadChunkSummaries(nextChunkId).catch(console.error)
        }, 100)
      }
    }
    
    // Apply text search filter
    let filtered = allPoems
    if (filters?.search) {
      const query = filters.search.toLowerCase()
      filtered = filtered.filter(p => 
        p.title?.toLowerCase().includes(query) ||
        p.author?.toLowerCase().includes(query)
      )
    }
    
    // Calculate the actual total based on filters
    let filteredTotal = index.metadata.total
    if (filters?.dynasty || filters?.genre) {
      // Estimate based on loaded chunks
      filteredTotal = relevantChunkIds.reduce((sum, id) => {
        const chunk = index.chunks.find(c => c.id === id)
        return sum + (chunk?.count || 0)
      }, 0)
    }
    
    const start = (page - 1) * pageSize
    return {
      poems: filtered.slice(start, start + pageSize),
      total: filtered.length,
      filteredTotal
    }
  }

  const getStats = async () => {
    const index = await loadIndex()
    return {
      total: index.metadata.total,
      chunks: index.metadata.chunks,
      dynasties: index.stats.dynasties,
      genres: index.stats.genres
    }
  }

  // Restore cached chunks from IndexedDB
  const restoreCachedChunks = async (): Promise<number[]> => {
    // Restore loaded chunk IDs
    const cachedIds = await getCachedMetadata()
    if (cachedIds && cachedIds.length > 0) {
      loadedChunkIds = [...cachedIds]
      // Preload chunks into memory cache
      for (const chunkId of cachedIds) {
        const cached = await getCachedChunkSummaries(chunkId)
        if (cached) {
          chunkCache.value.set(chunkId, cached)
        }
      }
    }
    return loadedChunkIds
  }

  // Clear all cache
  const clearAllCache = async () => {
    loadedChunkIds = []
    chunkCache.value.clear()
    indexCache.value = null
    const { clearCache } = await import('./usePoemCache')
    await clearCache()
  }

  return {
    loadIndex,
    loadChunkSummaries,
    loadChunkDetails,
    getPoemDetail,
    getAllPoems,
    getStats,
    restoreCachedChunks,
    clearAllCache,
    loading,
    loadingChunk,
    error
  }
}
