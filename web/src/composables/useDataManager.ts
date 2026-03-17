/**
 * DataManager - 统一数据管理系统
 * 
 * ## 概述
 * DataManager 是一个单例模式的数据管理类，提供统一的数据加载、缓存、转换接口。
 * 支持多种数据类型（诗词、诗人、词频、词境、搜索索引、关键词索引）的分块加载和持久化存储。
 * 
 * ## 核心功能
 * 1. 数据类型注册 - registerType() 注册数据类型配置
 * 2. 分块加载 - loadChunk() 从网络或缓存加载数据块
 * 3. 内存缓存 - LRU 策略的内存缓存，减少重复解析
 * 4. IndexedDB 持久化 - 使用 useCacheV2 存储已加载数据
 * 5. 统计订阅 - subscribe() 订阅数据加载状态变化
 * 6. 批量下载 - downloadAll() 支持批量下载所有分块
 * 
 * ## 数据流
 * ```
 * 请求 loadChunk(type, id)
 *     ↓
 * 检查内存缓存 → 有则返回
 *     ↓ 无
 * 检查 IndexedDB → 有则返回并写入内存缓存
 *     ↓ 无
 * 网络请求 → 解析 → 写入 IndexedDB → 写入内存缓存 → 返回
 * ```
 * 
 * ## 调用路径
 * 1. 初始化: initializeDataManager() 在应用启动时注册所有数据类型
 * 2. 数据页面: DataOverview/DataStorage 使用 getMetadata/getCache/clearStorage 直接操作
 * 3. 数据下载: 各 DownloadSection 使用对应的 composable (usePoemsV2, useKeywordIndex 等)
 * 4. 搜索功能: useSearchIndexV2, useKeywordIndex 等提供搜索数据
 * 
 * ## 支持的数据类型
 * - poems: 诗词数据 (CSV)
 * - authors: 诗人数据 (FBS)
 * - wordcount: 词频数据 (JSON)
 * - wordSimilarity: 词境/相似词 (FBS)
 * - poemIndex: 诗词搜索索引 (JSON)
 * - keywordIndex: 关键词索引 (JSON)
 */

import {
  getCache,
  setCache,
  getChunkedCache,
  setChunkedCache,
  getMetadata,
  setMetadata,
  getAllStorageStats,
  getStorageStats,
  type StorageStats
} from './useCacheV2'

export type DataType = 'poems' | 'authors' | 'wordcount' | 'wordSimilarity' | 'poemIndex' | 'keywordIndex'

export interface DataSourceConfig {
  urlPattern: string
  parser?: (data: any) => any
}

export interface DataTypeConfig {
  type: DataType
  storage: string
  sources: {
    raw?: DataSourceConfig
    processed?: DataSourceConfig
  }
  metadata: {
    url: string
    parser: (data: any) => any
  }
}

export interface DataStats {
  type: DataType
  raw: {
    totalChunks: number
    cachedChunks: number
    size: number
  }
  processed: {
    totalChunks: number
    cachedChunks: number
    size: number
  }
  memory: {
    cachedChunks: number
    size: number
  }
  status: 'idle' | 'loading' | 'converting' | 'error'
  lastUpdated: number
  error?: string
}

type StatsCallback = (stats: DataStats) => void
type Unsubscribe = () => void

class DataManager {
  private static instance: DataManager
  private configs: Map<DataType, DataTypeConfig> = new Map()
  private memoryCache: Map<string, { data: any; size: number; timestamp: number }> = new Map()
  private subscribers: Map<DataType, Set<StatsCallback>> = new Map()
  private maxMemoryItems = 50
  private maxMemorySize = 50 * 1024 * 1024

  private constructor() {}

  static getInstance(): DataManager {
    if (!DataManager.instance) {
      DataManager.instance = new DataManager()
    }
    return DataManager.instance
  }

  registerType(config: DataTypeConfig): void {
    this.configs.set(config.type, config)
  }

  private makeCacheKey(type: DataType, chunkId: number | string, format: 'raw' | 'processed' = 'processed'): string {
    return `${this.configs.get(type)?.storage || type}:${format}:chunk:${chunkId}`
  }

  async loadChunk(type: DataType, chunkId: number, format: 'raw' | 'processed' = 'processed'): Promise<any> {
    const config = this.configs.get(type)
    if (!config) {
      throw new Error(`Unknown data type: ${type}`)
    }

    const cacheKey = this.makeCacheKey(type, chunkId, format)

    const cached = this.memoryCache.get(cacheKey)
    if (cached) {
      return cached.data
    }

    const indexedDbData = await getChunkedCache<any>(config.storage, chunkId)
    if (indexedDbData) {
      this.cacheToMemory(cacheKey, indexedDbData)
      return indexedDbData
    }

    const source = format === 'raw' ? config.sources.raw : config.sources.processed
    if (!source) {
      throw new Error(`No source configured for ${type} (format: ${format})`)
    }

    const url = source.urlPattern.replace('{id}', chunkId.toString().padStart(4, '0'))
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to load ${type} chunk ${chunkId}: ${response.status}`)
    }

    let data: any
    if (source.parser) {
      const buffer = new Uint8Array(await response.arrayBuffer())
      data = await source.parser(buffer)
    } else {
      data = await response.json()
    }

    await setChunkedCache(config.storage, chunkId, data)
    this.cacheToMemory(cacheKey, data)

    await this.updateLoadedChunks(type, chunkId)

    return data
  }

  private async updateLoadedChunks(type: DataType, chunkId: number): Promise<void> {
    const config = this.configs.get(type)
    if (!config) return

    const meta = await getMetadata(config.storage)
    const loadedChunkIds = meta?.loadedChunkIds || []

    if (!loadedChunkIds.includes(chunkId)) {
      loadedChunkIds.push(chunkId)
      await setMetadata(config.storage, { loadedChunkIds })
    }
  }

  async loadChunks(type: DataType, chunkIds: number[], format: 'raw' | 'processed' = 'processed'): Promise<any[]> {
    const results: any[] = []
    for (const chunkId of chunkIds) {
      try {
        const data = await this.loadChunk(type, chunkId, format)
        results.push(data)
      } catch (error) {
        console.error(`Failed to load ${type} chunk ${chunkId}:`, error)
      }
    }
    return results
  }

  async getStats(type: DataType): Promise<DataStats> {
    const config = this.configs.get(type)
    if (!config) {
      throw new Error(`Unknown data type: ${type}`)
    }

    const storageStats = await getStorageStats(config.storage)
    const meta = await getMetadata(config.storage)

    return {
      type,
      raw: {
        totalChunks: 0,
        cachedChunks: 0,
        size: 0
      },
      processed: {
        totalChunks: meta?.totalChunks || 0,
        cachedChunks: meta?.loadedChunkIds?.length || 0,
        size: storageStats?.totalSize || 0
      },
      memory: {
        cachedChunks: this.getMemoryCacheCount(type),
        size: this.getMemoryCacheSize()
      },
      status: 'idle',
      lastUpdated: meta?.timestamp || 0
    }
  }

  async getAllStats(): Promise<Record<DataType, DataStats>> {
    const results: Partial<Record<DataType, DataStats>> = {}

    for (const type of this.configs.keys()) {
      try {
        results[type] = await this.getStats(type)
      } catch (error) {
        console.error(`Failed to get stats for ${type}:`, error)
      }
    }

    return results as Record<DataType, DataStats>
  }

  async clearCache(type?: DataType): Promise<void> {
    if (type) {
      const config = this.configs.get(type)
      if (config) {
        const { clearStorage } = await import('./useCacheV2')
        await clearStorage(config.storage)
        this.clearMemoryCache(type)
      }
    } else {
      for (const t of this.configs.keys()) {
        const config = this.configs.get(t)
        if (config) {
          const { clearStorage } = await import('./useCacheV2')
          await clearStorage(config.storage)
        }
      }
      this.memoryCache.clear()
    }

    this.notifySubscribers(type!)
  }

  async convertFormat(type: DataType, _targetFormat: 'json' = 'json'): Promise<{ success: number; failed: number }> {
    const config = this.configs.get(type)
    if (!config?.sources.raw) {
      return { success: 0, failed: 0 }
    }

    const meta = await getMetadata(config.storage)
    const chunkIds = meta?.loadedChunkIds || []

    let success = 0
    let failed = 0

    for (const chunkId of chunkIds) {
      try {
        const rawData = await this.loadChunk(type, chunkId, 'raw')
        await setChunkedCache(config.storage, chunkId, rawData)
        success++
      } catch (error) {
        console.error(`Failed to convert ${type} chunk ${chunkId}:`, error)
        failed++
      }
    }

    return { success, failed }
  }

  subscribe(type: DataType, callback: StatsCallback): Unsubscribe {
    if (!this.subscribers.has(type)) {
      this.subscribers.set(type, new Set())
    }
    this.subscribers.get(type)!.add(callback)

    return () => {
      this.subscribers.get(type)?.delete(callback)
    }
  }

  private notifySubscribers(type: DataType): void {
    const callbacks = this.subscribers.get(type)
    if (callbacks) {
      this.getStats(type).then(stats => {
        callbacks.forEach(cb => cb(stats))
      })
    }
  }

  private cacheToMemory(key: string, data: any): void {
    const size = JSON.stringify(data).length

    while (
      this.memoryCache.size >= this.maxMemoryItems ||
      this.getMemoryCacheSize() + size > this.maxMemorySize
    ) {
      const oldestKey = this.findOldestCacheKey()
      if (oldestKey) {
        this.memoryCache.delete(oldestKey)
      } else {
        break
      }
    }

    this.memoryCache.set(key, {
      data,
      size,
      timestamp: Date.now()
    })
  }

  private findOldestCacheKey(): string | null {
    let oldestKey: string | null = null
    let oldestTime = Infinity

    for (const [key, value] of this.memoryCache.entries()) {
      if (value.timestamp < oldestTime) {
        oldestTime = value.timestamp
        oldestKey = key
      }
    }

    return oldestKey
  }

  private clearMemoryCache(type: DataType): void {
    const prefix = this.configs.get(type)?.storage || type
    for (const key of this.memoryCache.keys()) {
      if (key.startsWith(prefix)) {
        this.memoryCache.delete(key)
      }
    }
  }

  private getMemoryCacheCount(type: DataType): number {
    const prefix = this.configs.get(type)?.storage || type
    let count = 0
    for (const key of this.memoryCache.keys()) {
      if (key.startsWith(prefix)) {
        count++
      }
    }
    return count
  }

  private getMemoryCacheSize(): number {
    let size = 0
    for (const value of this.memoryCache.values()) {
      size += value.size
    }
    return size
  }
}

export const dataManager = DataManager.getInstance()

export async function initializeDataManager(): Promise<void> {
  const { useWordSimilarityMetadata, useWordcountMetadata, usePoemIndexManifest } = await import('./useMetadataLoader')

  dataManager.registerType({
    type: 'wordSimilarity',
    storage: 'word-similarity-v2',
    sources: {
      raw: {
        urlPattern: 'data/word_similarity_v3/word_chunk_{id}.bin'
      }
    },
    metadata: {
      url: 'data/word_similarity_v3/metadata.json',
      parser: (data: any) => data
    }
  })

  dataManager.registerType({
    type: 'wordcount',
    storage: 'wordcount-v2',
    sources: {
      processed: {
        urlPattern: 'data/wordcount_v2/chunk_{id}.json'
      }
    },
    metadata: {
      url: 'data/wordcount_v2/meta.json',
      parser: (data: any) => data
    }
  })

  dataManager.registerType({
    type: 'poems',
    storage: 'poems-v2',
    sources: {
      processed: {
        urlPattern: 'data/preprocessed/poems_chunk_{id}.csv'
      }
    },
    metadata: {
      url: 'data/preprocessed/metadata.json',
      parser: (data: any) => data
    }
  })

  dataManager.registerType({
    type: 'poemIndex',
    storage: 'poem-index-v2',
    sources: {
      processed: {
        urlPattern: 'data/poem_index/poems_{id}.json'
      }
    },
    metadata: {
      url: 'data/poem_index/poem_index_manifest.json',
      parser: (data: any) => data
    }
  })

  dataManager.registerType({
    type: 'authors',
    storage: 'authors-v2',
    sources: {
      raw: {
        urlPattern: 'data/author_v2/author_chunk_{id}.fbs'
      }
    },
    metadata: {
      url: 'data/author_v2/authors-meta.json',
      parser: (data: any) => data
    }
  })

  dataManager.registerType({
    type: 'keywordIndex',
    storage: 'keyword-index-v2',
    sources: {
      processed: {
        urlPattern: 'data/keyword_index/keyword_{id}.json'
      }
    },
    metadata: {
      url: 'data/keyword_index/metadata.json',
      parser: (data: any) => data
    }
  })

  console.log('[DataManager] Initialized with types:', Array.from((dataManager as any).configs.keys()))
}
