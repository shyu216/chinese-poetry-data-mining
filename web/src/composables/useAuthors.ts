import { ref, shallowRef, computed } from 'vue'
import type { AuthorStats } from '@/types/author'
import { 
  cacheAuthors, 
  getCachedAuthors,
  cacheAuthorChunk,
  getCachedAuthorChunk,
  updateAuthorMetadata,
  getAuthorMetadata,
  getAllCachedAuthorChunks,
  areAllAuthorChunksCached,
  getCachedAuthorChunkIds
} from './usePoemCache'
import { loadAuthorChunkFbs, parseAuthorChunkFbs } from './useAuthorsFbs'

const authorsCache = shallowRef<AuthorStats[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const totalAuthors = ref(0)
const loadedCount = ref(0)
const isIncrementalLoading = ref(false)
const totalChunks = ref(0)

// Event emitter for incremental loading
const loadingCallbacks: ((authors: AuthorStats[], progress: number) => void)[] = []

// Loading control for pause/resume
let isLoadingPaused = false
let pauseResolver: (() => void) | null = null
let abortController: AbortController | null = null

/**
 * Check if page is visible
 */
function isPageVisible(): boolean {
  return document.visibilityState === 'visible'
}

/**
 * Wait until page becomes visible
 */
async function waitForVisible(): Promise<void> {
  if (isPageVisible()) return
  
  return new Promise(resolve => {
    const handler = () => {
      if (document.visibilityState === 'visible') {
        document.removeEventListener('visibilitychange', handler)
        resolve()
      }
    }
    document.addEventListener('visibilitychange', handler)
  })
}

/**
 * Wait until loading is resumed
 */
async function waitForResume(): Promise<void> {
  if (!isLoadingPaused) return
  
  return new Promise(resolve => {
    pauseResolver = () => {
      pauseResolver = null
      resolve()
    }
  })
}

/**
 * Pause loading
 */
export function pauseLoading(): void {
  isLoadingPaused = true
  console.log('⏸️ Author loading paused')
}

/**
 * Resume loading
 */
export function resumeLoading(): void {
  isLoadingPaused = false
  if (pauseResolver) {
    pauseResolver()
  }
  console.log('▶️ Author loading resumed')
}

/**
 * Check if loading is paused
 */
export function isPaused(): boolean {
  return isLoadingPaused
}

// Metadata cache
interface AuthorChunkMeta {
  index: number
  filename: string
  authorCount?: number
}

interface AuthorsMeta {
  total: number
  totalAuthors?: number
  chunks: AuthorChunkMeta[]
}

let metaPromise: Promise<AuthorsMeta> | null = null

async function loadAuthorsMeta(): Promise<AuthorsMeta> {
  if (metaPromise) return metaPromise
  
  metaPromise = fetch(`${import.meta.env.BASE_URL}data/author_v2/authors-meta.json`)
    .then(r => {
      if (!r.ok) throw new Error('Failed to load authors metadata')
      return r.json()
    })
    .catch(e => {
      console.warn('Failed to load authors-meta.json, using fallback:', e)
      // Fallback: assume 857 chunks if meta file not found
      return {
        total: 857,
        chunks: Array.from({ length: 857 }, (_, i) => ({
          index: i,
          filename: `author_chunk_${i.toString().padStart(4, '0')}.fbs`
        }))
      }
    })
  
  return metaPromise
}



export function useAuthors() {
  const onIncrementalLoad = (callback: (authors: AuthorStats[], progress: number) => void) => {
    loadingCallbacks.push(callback)
    return () => {
      const index = loadingCallbacks.indexOf(callback)
      if (index > -1) loadingCallbacks.splice(index, 1)
    }
  }

  const notifyIncrementalLoad = (authors: AuthorStats[], progress: number) => {
    loadingCallbacks.forEach(cb => cb(authors, progress))
  }

  /**
   * Load authors sequentially from FBS files - fetch one by one for better UX
   * Since files are already sorted (0000 = #1, 0001 = #2, etc.)
   * we can render immediately as each file loads
   * 
   * NEW: Incremental caching - each chunk is cached to IndexedDB as soon as loaded
   * This allows resuming from where user left off if they close the browser
   */
  const loadAllAuthors = async (incremental = false, options?: { delay?: number; batchSize?: number }): Promise<AuthorStats[]> => {
    // Priority 1: Check if already loading
    if (loading.value) {
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!loading.value && authorsCache.value.length > 0) {
            clearInterval(checkInterval)
            resolve(authorsCache.value)
          }
        }, 100)
      })
    }

    loading.value = true
    isIncrementalLoading.value = incremental
    error.value = null
    loadedCount.value = 0

    const authors: AuthorStats[] = []
    
    // Default: 50ms delay between requests, batch 10 at a time for UI updates
    const delay = options?.delay ?? 50
    const batchSize = options?.batchSize ?? 10
    
    try {
      // Load metadata first to know how many chunks to load
      const meta = await loadAuthorsMeta()
      totalChunks.value = meta.total
      
      // Get total authors count from meta if available
      const totalAuthorsCount = meta.totalAuthors || meta.total
      totalAuthors.value = totalAuthorsCount  // Update the global ref
      
      // Check which chunks are already cached in IndexedDB
      const cachedChunkIds = await getCachedAuthorChunkIds()
      const chunksToLoad = meta.chunks.filter(chunk => !cachedChunkIds.includes(chunk.index))
      
      // If all chunks are cached, load from IndexedDB
      if (chunksToLoad.length === 0 && cachedChunkIds.length === meta.total) {
        const allCached = await getAllCachedAuthorChunks()
        if (allCached && allCached.length > 0) {
          authorsCache.value = allCached
          totalAuthors.value = allCached.length
          loading.value = false
          isIncrementalLoading.value = false
          return allCached
        }
      }
      
      // Load already cached chunks first for immediate display
      if (cachedChunkIds.length > 0) {
        for (const chunkId of cachedChunkIds) {
          const cachedChunk = await getCachedAuthorChunk(chunkId)
          if (cachedChunk) {
            authors.push(...cachedChunk)
          }
        }
        loadedCount.value = authors.length
        
        // Notify with cached data immediately
        if (incremental && authors.length > 0) {
          const progress = Math.round(authors.length / totalAuthorsCount * 100)
          notifyIncrementalLoad([...authors], progress)
        }
      }
      
      // Create abort controller for this loading session
      abortController = new AbortController()
      const signal = abortController.signal
      
      // Load remaining chunks that are not cached
      for (let i = 0; i < chunksToLoad.length; i++) {
        // Check if loading was aborted
        if (signal.aborted) {
          console.log('Author loading aborted')
          break
        }
        
        // Pause loading when page is not visible to save resources
        if (!isPageVisible()) {
          console.log('Page hidden, pausing author loading...')
          await waitForVisible()
          console.log('Page visible, resuming author loading...')
        }
        
        // Check if manually paused
        if (isLoadingPaused) {
          console.log('⏸️ Loading manually paused, waiting...')
          await waitForResume()
          console.log('▶️ Loading manually resumed')
        }
        
        const chunkMeta = chunksToLoad[i]
        if (!chunkMeta) continue
        const chunkId = chunkMeta.index.toString().padStart(4, '0')
        const chunkIndex = chunkMeta.index
        
        try {
          // Load FBS format
          const chunkAuthors = await loadAuthorChunkFbs(chunkId)
          
          // Add to memory
          authors.push(...chunkAuthors)
          loadedCount.value = authors.length
          
          // IMMEDIATELY cache this chunk to IndexedDB (incremental caching)
          await cacheAuthorChunk(chunkIndex, chunkAuthors)
          await updateAuthorMetadata(chunkIndex, meta.total)
          
          // Notify for incremental rendering (every batchSize chunks)
          if (incremental) {
            const progress = Math.round(authors.length / totalAuthorsCount * 100)
            notifyIncrementalLoad([...authors], progress)
            // Give UI time to render
            await new Promise(resolve => setTimeout(resolve, 0))
          }
        } catch (e) {
          console.warn(`Error loading chunk ${chunkId}:`, e)
          // Continue loading other chunks
        }
        
        // Rate limiting: add delay between requests to prevent overwhelming the browser
        // Skip delay for the last chunk
        if (i < chunksToLoad.length - 1) {
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }
      
      // Final notification with complete data
      if (incremental) {
        notifyIncrementalLoad([...authors], 100)
      }
      
      authorsCache.value = authors
      totalAuthors.value = authors.length
      
      // Also cache all authors as a single entry for backward compatibility
      await cacheAuthors(authors)
      
      return authors
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      throw e
    } finally {
      loading.value = false
      isIncrementalLoading.value = false
    }
  }

  /**
   * Load only top N authors for quick initial display
   */
  const loadTopAuthors = async (count: number = 20): Promise<AuthorStats[]> => {
    if (authorsCache.value.length >= count) {
      return authorsCache.value.slice(0, count)
    }

    const authors: AuthorStats[] = []
    
    try {
      const meta = await loadAuthorsMeta()
      const chunksToLoad = meta.chunks.slice(0, Math.min(count, meta.total))
      
      for (const chunk of chunksToLoad) {
        const chunkId = chunk.index.toString().padStart(4, '0')
        
        try {
          const chunkAuthors = await loadAuthorChunkFbs(chunkId)
          authors.push(...chunkAuthors)
        } catch (e) {
          console.warn(`Error loading chunk ${chunkId}:`, e)
        }
      }
      
      return authors
    } catch (e) {
      console.error('Error loading top authors:', e)
      return authors
    }
  }

  const getTopAuthors = (limit: number = 100): AuthorStats[] => {
    return authorsCache.value.slice(0, limit)
  }

  const getAuthorsByDynasty = (dynasty: string): AuthorStats[] => {
    return authorsCache.value
  }

  const searchAuthors = (query: string): AuthorStats[] => {
    if (!query.trim()) return authorsCache.value
    
    const lowerQuery = query.toLowerCase()
    return authorsCache.value.filter(author => 
      author.author.toLowerCase().includes(lowerQuery)
    )
  }

  const getAuthorStats = () => ({
    total: totalAuthors.value,
    topAuthor: authorsCache.value[0]?.author || '',
    maxPoems: authorsCache.value[0]?.poem_count || 0
  })

  /**
   * Abort ongoing loading
   * When aborted, clear memory cache so next visit will reload
   */
  const abortLoading = () => {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    // Clear memory cache if loading was aborted (incomplete data)
    // IndexedDB cache is only written after complete load, so it's safe
    if (loading.value) {
      authorsCache.value = []
      loading.value = false
      isIncrementalLoading.value = false
    }
  }

  return {
    loadAllAuthors,
    loadTopAuthors,
    getTopAuthors,
    getAuthorsByDynasty,
    searchAuthors,
    getAuthorStats,
    onIncrementalLoad,
    abortLoading,
    pauseLoading,
    resumeLoading,
    isPaused,
    authors: computed(() => authorsCache.value),
    loading,
    error,
    loadedCount,
    totalChunks: computed(() => totalChunks.value),
    totalAuthors: computed(() => totalAuthors.value),
    isIncrementalLoading
  }
}

// Export meta loading function for external use
export { loadAuthorsMeta }
