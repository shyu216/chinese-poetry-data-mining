import { ref, shallowRef, computed } from 'vue'
import type { AuthorStats } from '@/types/author'
import { cacheAuthors, getCachedAuthors } from './usePoemCache'
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
   */
  const loadAllAuthors = async (incremental = false, options?: { delay?: number; batchSize?: number }): Promise<AuthorStats[]> => {
    if (authorsCache.value.length > 0) {
      return authorsCache.value
    }

    // Try cache first - now stores FBS binary data
    const cached = await getCachedAuthors()
    if (cached && cached.length > 0) {
      authorsCache.value = cached
      totalAuthors.value = cached.length
      return cached
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
      
      // Create abort controller for this loading session
      abortController = new AbortController()
      const signal = abortController.signal
      
      // Sequential loading with rate limiting and visibility check
      // This prevents browser from being overwhelmed by too many concurrent requests
      for (let i = 0; i < meta.chunks.length; i++) {
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
        
        const chunkMeta = meta.chunks[i]
        if (!chunkMeta) continue
        const chunkId = chunkMeta.index.toString().padStart(4, '0')
        
        try {
          // Load FBS format
          const chunkAuthors = await loadAuthorChunkFbs(chunkId)
          authors.push(...chunkAuthors)
          loadedCount.value = authors.length
          
          // Notify for incremental rendering (every batchSize chunks)
          if (incremental && (i + 1) % batchSize === 0) {
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
        if (i < meta.chunks.length - 1) {
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }
      
      // Final notification with complete data
      if (incremental) {
        notifyIncrementalLoad([...authors], 100)
      }
      
      authorsCache.value = authors
      totalAuthors.value = authors.length
      
      // Cache to IndexedDB (stores the parsed AuthorStats)
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
   */
  const abortLoading = () => {
    if (abortController) {
      abortController.abort()
      abortController = null
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
    authors: computed(() => authorsCache.value),
    loading,
    error,
    loadedCount,
    totalChunks: computed(() => totalChunks.value),
    totalAuthors: computed(() => totalAuthors.value),
    isIncrementalLoading
  }
}
