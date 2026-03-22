import { ref, onUnmounted } from 'vue'
import type { WorkerMessage, WorkerResponse } from '@/workers/dataProcessor.worker'

let workerInstance: Worker | null = null
let messageId = 0
const pendingMessages = new Map<string, { resolve: (value: unknown) => void; reject: (reason: Error) => void }>()

function getWorker(): Worker {
  if (!workerInstance) {
    workerInstance = new Worker(new URL('@/workers/dataProcessor.worker.ts', import.meta.url), {
      type: 'module'
    })
    
    workerInstance.onmessage = (event: MessageEvent<WorkerResponse | { type: 'progress'; progress: number }>) => {
      const data = event.data
      
      if (data.type === 'progress') {
        // 进度更新，可以在这里处理
        return
      }
      
      const { id, type, result, error } = data as WorkerResponse
      const pending = pendingMessages.get(id)
      
      if (pending) {
        if (type === 'success') {
          pending.resolve(result)
        } else {
          pending.reject(new Error(error || 'Worker error'))
        }
        pendingMessages.delete(id)
      }
    }
    
    workerInstance.onerror = (error) => {
      console.error('Worker error:', error)
    }
  }
  
  return workerInstance
}

export function useWorker() {
  const isProcessing = ref(false)
  const progress = ref(0)
  const error = ref<string | null>(null)
  
  async function sendMessage<T>(type: WorkerMessage['type'], payload: unknown): Promise<T> {
    isProcessing.value = true
    progress.value = 0
    error.value = null
    
    const id = `${Date.now()}-${++messageId}`
    const worker = getWorker()
    
    return new Promise<T>((resolve, reject) => {
      pendingMessages.set(id, { 
        resolve: (result) => {
          isProcessing.value = false
          resolve(result as T)
        }, 
        reject: (err) => {
          isProcessing.value = false
          error.value = err.message
          reject(err)
        } 
      })
      
      const message: WorkerMessage = { type, payload, id }
      worker.postMessage(message)
    })
  }
  
  // 词频统计
  async function processWordCount(words: string[], texts: string[]): Promise<Map<string, number>> {
    // Worker 无法传递 Map，需要转换为普通对象
    const result = await sendMessage<Record<string, number>>('processWordCount', { words, texts })
    return new Map(Object.entries(result))
  }
  
  // 相似度计算
  async function processSimilarity(vectors: number[][], query: number[], topK: number): Promise<{ index: number; score: number }[]> {
    return sendMessage('processSimilarity', { vectors, query, topK })
  }
  
  // 数据排序
  async function sortData<T>(items: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): Promise<T[]> {
    return sendMessage('sortData', { items, key, order })
  }
  
  // 终止 Worker
  function terminate() {
    if (workerInstance) {
      workerInstance.terminate()
      workerInstance = null
      pendingMessages.clear()
    }
  }
  
  onUnmounted(() => {
    // 不在这里终止，因为 Worker 是全局共享的
  })
  
  return {
    isProcessing,
    progress,
    error,
    processWordCount,
    processSimilarity,
    sortData,
    terminate
  }
}
