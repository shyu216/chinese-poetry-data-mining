// 数据处理 Web Worker
// 用于在后台线程处理大量数据，避免阻塞主线程

export interface WorkerMessage {
  type: 'processWordCount' | 'processSimilarity' | 'sortData' | 'filterData'
  payload: unknown
  id: string
}

export interface WorkerResponse {
  type: 'success' | 'error'
  result?: unknown
  error?: string
  id: string
}

// 词频统计处理
function processWordCount(data: { words: string[]; texts: string[] }): Map<string, number> {
  const wordCount = new Map<string, number>()
  const { words, texts } = data
  
  // 批量处理，每1000条让出一次
  const batchSize = 1000
  
  for (let i = 0; i < texts.length; i++) {
    const text = texts[i]!
    
    for (const word of words) {
      // 使用正则匹配词
      const regex = new RegExp(word, 'g')
      const matches = text.match(regex)
      if (matches) {
        wordCount.set(word, (wordCount.get(word) || 0) + matches.length)
      }
    }
    
    // 每处理1000条，让出时间片
    if (i % batchSize === 0) {
      self.postMessage({ type: 'progress', progress: i / texts.length })
    }
  }
  
  return wordCount
}

// 相似度计算处理
function processSimilarity(data: { vectors: number[][]; query: number[]; topK: number }): { index: number; score: number }[] {
  const { vectors, query, topK } = data
  const scores: { index: number; score: number }[] = []
  
  for (let i = 0; i < vectors.length; i++) {
    const vector = vectors[i]!
    // 计算余弦相似度
    let dotProduct = 0
    let normA = 0
    let normB = 0
    
    for (let j = 0; j < vector.length; j++) {
      const a = vector[j]!
      const b = query[j]!
      dotProduct += a * b
      normA += a * a
      normB += b * b
    }
    
    const similarity = dotProduct / (Math.sqrt(normA) * Math.sqrt(normB))
    scores.push({ index: i, score: similarity })
    
    // 每1000条让出一次
    if (i % 1000 === 0) {
      self.postMessage({ type: 'progress', progress: i / vectors.length })
    }
  }
  
  // 返回前K个最相似的
  return scores
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
}

// 数据排序
function sortData<T extends Record<string, unknown>>(data: { items: T[]; key: keyof T; order: 'asc' | 'desc' }): T[] {
  const { items, key, order } = data
  const sorted = [...items].sort((a, b) => {
    const aVal = a[key]
    const bVal = b[key]
    
    if (aVal === undefined || bVal === undefined) return 0
    if (aVal === null || bVal === null) return 0
    if (typeof aVal !== typeof bVal) return 0
    
    if (aVal < bVal) return order === 'asc' ? -1 : 1
    if (aVal > bVal) return order === 'asc' ? 1 : -1
    return 0
  })
  
  return sorted
}

// 数据过滤
function filterData<T>(data: { items: T[]; predicate: (item: T) => boolean }): T[] {
  return data.items.filter(data.predicate)
}

// 监听消息
self.onmessage = (event: MessageEvent<WorkerMessage>) => {
  const { type, payload, id } = event.data
  
  try {
    let result: unknown
    
    switch (type) {
      case 'processWordCount':
        result = processWordCount(payload as { words: string[]; texts: string[] })
        break
      case 'processSimilarity':
        result = processSimilarity(payload as { vectors: number[][]; query: number[]; topK: number })
        break
      case 'sortData':
        result = sortData(payload as { items: Record<string, unknown>[]; key: string; order: 'asc' | 'desc' })
        break
      case 'filterData':
        result = filterData(payload as { items: unknown[]; predicate: (item: unknown) => boolean })
        break
      default:
        throw new Error(`Unknown message type: ${type}`)
    }
    
    const response: WorkerResponse = {
      type: 'success',
      result,
      id
    }
    self.postMessage(response)
  } catch (error) {
    const response: WorkerResponse = {
      type: 'error',
      error: error instanceof Error ? error.message : String(error),
      id
    }
    self.postMessage(response)
  }
}

export {}
