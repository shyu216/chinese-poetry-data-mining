import { ref, computed, onUnmounted } from 'vue'

export interface ChunkLoaderOptions {
  chunkDelay?: number
  concurrency?: number  // 并发数，默认5
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

  /**
   * 并行加载 chunks，使用队列控制并发
   */
  async function loadChunks<T>(
    chunkIds: number[],
    loadFn: (chunkId: number, signal: AbortSignal) => Promise<T>,
    options: ChunkLoaderOptions = {}
  ): Promise<T[]> {
    const { 
      chunkDelay = 0,  // 默认移除延迟
      concurrency = 5,  // 默认5个并发
      onProgress, 
      onChunkLoaded, 
      onComplete, 
      onError 
    } = options

    isLoading.value = true
    isPaused.value = false
    loadedCount.value = 0
    totalCount.value = chunkIds.length
    abortController.value = new AbortController()

    const results: (T | null)[] = new Array(chunkIds.length).fill(null)
    let completedCount = 0
    let currentIndex = 0

    // 检查是否应该中止
    const shouldAbort = () => abortController.value?.signal.aborted ?? false

    // 等待暂停恢复
    const waitIfPaused = async () => {
      while (isPaused.value && !shouldAbort()) {
        await sleep(50)  // 减少检查频率
      }
    }

    // 单个 chunk 加载任务
    const loadSingleChunk = async (index: number): Promise<void> => {
      if (shouldAbort()) return

      await waitIfPaused()
      if (shouldAbort()) return

      const chunkId = chunkIds[index]!
      
      try {
        const data = await loadFn(chunkId, abortController.value!.signal)
        results[index] = data
        completedCount++
        loadedCount.value = completedCount

        onProgress?.(completedCount, totalCount.value)
        onChunkLoaded?.(chunkId, data)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          return
        }
        console.error(`Failed to load chunk ${chunkId}:`, error)
        completedCount++
        loadedCount.value = completedCount
        onError?.(error as Error)
      }
    }

    // 工作线程 - 持续从队列取任务执行
    const worker = async () => {
      while (currentIndex < chunkIds.length) {
        if (shouldAbort()) break
        
        const index = currentIndex++
        if (index < chunkIds.length) {
          await loadSingleChunk(index)
          // 可选的延迟，用于控制请求频率
          if (chunkDelay > 0 && currentIndex < chunkIds.length) {
            await sleep(chunkDelay)
          }
        }
      }
    }

    try {
      // 启动并发工作线程
      const workers: Promise<void>[] = []
      for (let i = 0; i < Math.min(concurrency, chunkIds.length); i++) {
        workers.push(worker())
      }

      await Promise.all(workers)

      if (!shouldAbort()) {
        onComplete?.()
      }
    } finally {
      isLoading.value = false
      abortController.value = null
    }

    return results.filter((r): r is T => r !== null)
  }

  /**
   * 快速批量加载 - 无延迟，最大并发
   */
  async function loadChunksFast<T>(
    chunkIds: number[],
    loadFn: (chunkId: number, signal: AbortSignal) => Promise<T>,
    options: Omit<ChunkLoaderOptions, 'chunkDelay' | 'concurrency'> = {}
  ): Promise<T[]> {
    return loadChunks(chunkIds, loadFn, {
      ...options,
      concurrency: 10,  // 最大并发
      chunkDelay: 0     // 无延迟
    })
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
    loadChunksFast,
    pause,
    resume,
    stop,
    reset
  }
}
