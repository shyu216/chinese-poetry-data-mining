/**
 * 文件: web/src/composables/useChunkLoader.ts
 * 说明: 通用的分片（chunk）加载器，提供并发控制、暂停/恢复、取消以及进度回调功能，用于所有需要按块下载并入本地缓存的数据集。
 *
 * 数据管线:
 *   - 接收待下载的 chunkId 列表与单 chunk 的加载函数 `loadFn`。
 *   - 使用内部队列与 worker 模式并发执行加载任务，支持 `concurrency`、`chunkDelay` 控制请求速率。
 *   - 在每个 chunk 加载完成后通过 `onChunkLoaded` 回调将数据回写本地缓存并更新进度。
 *
 * 复杂度:
 *   - 总体为 O(t)（t = 待下载分片数），单个 chunk 加载成本取决于 `loadFn` 的实现（如 JSON/CSV 解析成本）。
 *
 * 关键特性:
 *   - 支持暂停/恢复（`isPaused`）、取消（AbortController）和并发限制。
 *   - 将下载偏好（autoLoadOnEnter）持久化到 localStorage，便于用户控制自动加载策略。
 *
 * 风险与建议:
 *   - 需要合理设置并发上限与 chunkDelay，避免对服务器造成突发压力或触发限流。
 *   - 如果 `loadFn` 在主线程进行大量解析，应将解析迁移到 Web Worker，或减少单分片大小以避免 UI 卡顿。
 */
import { ref, computed, onUnmounted } from 'vue'

/** 各页面独立的 localStorage key，默认「进入页面不自动加载网络分块」 */
export const CHUNK_LOADER_PREFERENCE_KEYS = {
  poems: 'chunkLoader:autoLoadOnEnter:poems',
  authors: 'chunkLoader:autoLoadOnEnter:authors',
  wordcount: 'chunkLoader:autoLoadOnEnter:wordcount',
  wordcountWordSim: 'chunkLoader:autoLoadOnEnter:wordcount:wordSim'
} as const

const DEFAULT_PREFERENCE_KEY = 'chunkLoader:autoLoadOnEnter:default'

export interface UseChunkLoaderOptions {
  /** localStorage 键；不传则用 default（下载页等） */
  preferenceKey?: string
}

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

export function useChunkLoader(options?: UseChunkLoaderOptions) {
  const preferenceKey = options?.preferenceKey ?? DEFAULT_PREFERENCE_KEY

  const isLoading = ref(false)
  const isPaused = ref(false)
  const loadedCount = ref(0)
  const totalCount = ref(0)
  const currentChunkId = ref(0)
  const abortController = ref<AbortController | null>(null)

  /** 进入页面是否自动开始拉取未缓存分块；默认 false，存 localStorage */
  const autoLoadEnabled = ref(false)

  const loadAutoLoadSetting = () => {
    try {
      const stored = localStorage.getItem(preferenceKey)
      if (stored === null) {
        autoLoadEnabled.value = false
        console.log(
          `[useChunkLoader] preference missing key="${preferenceKey}" → autoLoadOnEnter=false (default)`
        )
      } else {
        autoLoadEnabled.value = stored === 'true'
        console.log(
          `[useChunkLoader] preference loaded key="${preferenceKey}" autoLoadOnEnter=${autoLoadEnabled.value}`
        )
      }
    } catch (e) {
      console.warn(`[useChunkLoader] failed to read preference key="${preferenceKey}"`, e)
    }
  }

  loadAutoLoadSetting()

  const saveAutoLoadSetting = (value: boolean, source: 'pause' | 'resume' | 'toggle' | 'api' = 'api') => {
    try {
      localStorage.setItem(preferenceKey, String(value))
      autoLoadEnabled.value = value
      const via =
        source === 'pause'
          ? '用户点击「暂停」'
          : source === 'resume'
            ? '用户点击「继续」'
            : source === 'toggle'
              ? 'toggle/enable/disable API'
              : 'saveAutoLoadSetting()'
      console.log(
        `[useChunkLoader] ${via} → preference saved key="${preferenceKey}" autoLoadOnEnter=${value}`
      )
    } catch (e) {
      console.warn(`[useChunkLoader] failed to save preference key="${preferenceKey}"`, e)
    }
  }

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
   * 如果 autoLoadEnabled 为 false，则初始状态为暂停，等待用户手动开始
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

    // 如果自动加载被禁用，初始状态设为暂停
    const shouldStartPaused = !autoLoadEnabled.value
    
    isLoading.value = true
    isPaused.value = shouldStartPaused  // 根据 autoLoadEnabled 决定是否暂停
    loadedCount.value = 0
    totalCount.value = chunkIds.length
    abortController.value = new AbortController()
    
    if (shouldStartPaused) {
      console.log(
        `[useChunkLoader] autoLoadOnEnter=false (key="${preferenceKey}"), workers idle until resume()`
      )
    }

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

  /** 与 ChunkLoader「暂停」联动：写入 localStorage，下次进入默认不自动拉未缓存分块 */
  function pause(): void {
    isPaused.value = true
    saveAutoLoadSetting(false, 'pause')
  }

  /** 与 ChunkLoader「继续」联动：写入 localStorage，下次进入自动拉未缓存分块 */
  function resume(): void {
    isPaused.value = false
    saveAutoLoadSetting(true, 'resume')
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

  /**
   * 启用自动加载（保存到 localStorage）
   */
  function enableAutoLoad(): void {
    saveAutoLoadSetting(true, 'api')
  }

  function disableAutoLoad(): void {
    saveAutoLoadSetting(false, 'api')
  }

  function toggleAutoLoad(): boolean {
    const newValue = !autoLoadEnabled.value
    saveAutoLoadSetting(newValue, 'toggle')
    return newValue
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
    autoLoadEnabled,
    preferenceKey,
    loadChunks,
    loadChunksFast,
    pause,
    resume,
    stop,
    reset,
    saveAutoLoadSetting,
    enableAutoLoad,
    disableAutoLoad,
    toggleAutoLoad
  }
}
