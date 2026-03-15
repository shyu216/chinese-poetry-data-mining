import { ref, shallowRef, computed } from 'vue'
import type { AuthorStats } from '@/types/author'
import { cacheAuthors, getCachedAuthors } from './usePoemCache'

const authorsCache = shallowRef<AuthorStats[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const totalAuthors = ref(0)
const loadedCount = ref(0)
const isIncrementalLoading = ref(false)

// Event emitter for incremental loading
const loadingCallbacks: ((authors: AuthorStats[], progress: number) => void)[] = []

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

  const loadAllAuthors = async (incremental = false): Promise<AuthorStats[]> => {
    if (authorsCache.value.length > 0) {
      return authorsCache.value
    }

    // Try cache first
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

    try {
      const authors: AuthorStats[] = []
      const totalChunks = 857 // Total author chunks
      
      // Load chunks in batches for incremental display
      const batchSize = 10 // Load 10 at a time
      
      for (let batchStart = 0; batchStart < totalChunks; batchStart += batchSize) {
        const batchEnd = Math.min(batchStart + batchSize, totalChunks)
        const batchPromises = []
        
        for (let i = batchStart; i < batchEnd; i++) {
          const chunkId = i.toString().padStart(4, '0')
          batchPromises.push(
            fetch(`/data/author/author_chunk_${chunkId}.json`)
              .then(response => {
                if (!response.ok) throw new Error(`Failed to load ${i}`)
                return response.json()
              })
              .catch(() => null)
          )
        }
        
        const batchResults = await Promise.all(batchPromises)
        const validAuthors = batchResults.filter((a): a is AuthorStats => a !== null)
        authors.push(...validAuthors)
        
        loadedCount.value = authors.length
        
        // Notify incremental loading - top authors first (already sorted by poem count)
        if (incremental && batchStart < 100) { // Only for first 100
          const progress = Math.round((batchEnd / Math.min(100, totalChunks)) * 100)
          notifyIncrementalLoad([...authors], progress)
        }
      }
      
      // Sort by poem count descending (should already be sorted)
      authors.sort((a, b) => b.poem_count - a.poem_count)
      
      authorsCache.value = authors
      totalAuthors.value = authors.length
      
      // Cache to IndexedDB
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

  return {
    loadAllAuthors,
    getTopAuthors,
    getAuthorsByDynasty,
    searchAuthors,
    getAuthorStats,
    onIncrementalLoad,
    authors: computed(() => authorsCache.value),
    loading,
    error,
    loadedCount,
    isIncrementalLoading
  }
}
