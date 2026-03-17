import { ref, computed, onUnmounted } from 'vue'

export interface ChunkLoaderOptions {
  chunkDelay?: number
  onProgress?: (loaded: number, total: number) => void
  onChunkLoaded?: (chunkId: number, data: unknown) => void
  onComplete?: () => void
  onError?: (error: Error) => void
}

export interface ChunkLoaderState {
  isLoading: boolean
  isPaused: boolean
  progress: number
  loadedCount: number
  totalCount: number
}

export function useChunkLoader() {
  const isLoading = ref(false)
  const isPaused = ref(false)
  const loadedCount = ref(0)
  const totalCount = ref(0)
  const currentChunkId = ref(0)
  const abortController = ref<AbortController | null>(null)

  const progress = computed(() => {
    if (totalCount.value === 0) return 0
    return Math.round((loadedCount.value / totalCount.value) * 100)
  })

  const state = computed<ChunkLoaderState>(() => ({
    isLoading: isLoading.value,
    isPaused: isPaused.value,
    progress: progress.value,
    loadedCount: loadedCount.value,
    totalCount: totalCount.value
  }))

  function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  async function loadChunks<T>(
    chunkIds: number[],
    loadFn: (chunkId: number, signal: AbortSignal) => Promise<T>,
    options: ChunkLoaderOptions = {}
  ): Promise<T[]> {
    const { chunkDelay = 100, onProgress, onChunkLoaded, onComplete, onError } = options

    isLoading.value = true
    isPaused.value = false
    loadedCount.value = 0
    totalCount.value = chunkIds.length
    currentChunkId.value = 0
    abortController.value = new AbortController()

    const results: T[] = []

    try {
      for (let i = 0; i < chunkIds.length; i++) {
        if (abortController.value.signal.aborted) {
          break
        }

        while (isPaused.value && !abortController.value.signal.aborted) {
          await sleep(100)
        }

        if (abortController.value.signal.aborted) {
          break
        }

        const chunkId = chunkIds[i]!
        currentChunkId.value = chunkId

        try {
          const data = await loadFn(chunkId, abortController.value.signal)
          results.push(data)
          loadedCount.value++

          onProgress?.(loadedCount.value, totalCount.value)
          onChunkLoaded?.(chunkId, data)
        } catch (error) {
          if (error instanceof Error && error.name === 'AbortError') {
            break
          }
          console.error(`Failed to load chunk ${chunkId}:`, error)
          onError?.(error as Error)
        }

        if (i < chunkIds.length - 1 && chunkDelay > 0) {
          await sleep(chunkDelay)
        }
      }

      if (!abortController.value.signal.aborted) {
        onComplete?.()
      }
    } finally {
      isLoading.value = false
      abortController.value = null
    }

    return results
  }

  function pause(): void {
    isPaused.value = true
  }

  function resume(): void {
    isPaused.value = false
  }

  function stop(): void {
    abortController.value?.abort()
    isLoading.value = false
    isPaused.value = false
  }

  function reset(): void {
    stop()
    loadedCount.value = 0
    totalCount.value = 0
    currentChunkId.value = 0
  }

  onUnmounted(() => {
    stop()
  })

  return {
    isLoading,
    isPaused,
    progress,
    loadedCount,
    totalCount,
    currentChunkId,
    state,
    loadChunks,
    pause,
    resume,
    stop,
    reset
  }
}
