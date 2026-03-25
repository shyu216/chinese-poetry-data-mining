/**
 * @overview
 * file: web/src/search/word/WordSearch.ts
 * category: algorithm
 * tech: TypeScript
 * solved: 实现检索与索引策略（核心导出：wordSearch, WordSearchResult, WordSearchOptions）
 * data_source: public/data 静态分块文件
 * data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
 * complexity: 常见查询/筛选 O(n)，排序 O(n log n)，空间复杂度常见 O(n)
 * unique: 核心导出: wordSearch, WordSearchResult, WordSearchOptions
 */
/**
 * WordSearch - 词汇搜索模块
 *
 * 职责：
 * 1. 从 wordcount_v2 加载词频数据
 * 2. 构建词汇索引（支持按词长度、频次筛选）
 * 3. 支持词汇搜索、相似词查找
 * 4. LRU 缓存搜索结果
 */

import { LRUCache } from '../LRUCache'
import type { WordCountItem } from '@/composables/types'

export interface WordSearchResult {
  items: WordCountItem[]
  total: number
  queryTime: number
  source: 'memory' | 'cache'
}

export interface WordSearchOptions {
  limit?: number
  offset?: number
  filters?: {
    minLength?: number
    maxLength?: number
    minCount?: number
    maxCount?: number
  }
}

class WordSearch {
  private static instance: WordSearch

  // 词汇数据缓存
  private words = new Map<string, WordCountItem>()

  // 长度索引: 词长度 -> 词汇列表
  private lengthIndex = new Map<number, string[]>()

  // 频次排序列表（按频次降序）
  private wordsByFrequency: WordCountItem[] = []

  // LRU 缓存
  private searchCache = new LRUCache<WordSearchResult>(500, 5 * 60 * 1000)

  // 状态
  private isInitialized = false
  private isLoading = false
  private initPromise: Promise<void> | null = null

  // 统计
  private stats = {
    totalWords: 0,
    loadedChunks: 0,
    totalChunks: 0
  }

  private constructor() {}

  static getInstance(): WordSearch {
    if (!WordSearch.instance) {
      WordSearch.instance = new WordSearch()
    }
    return WordSearch.instance
  }

  // ============ 初始化 ============

  async initialize(): Promise<void> {
    if (this.isInitialized) return
    if (this.isLoading && this.initPromise) return this.initPromise

    this.isLoading = true
    this.initPromise = this.doInitialize()
    return this.initPromise
  }

  private async doInitialize(): Promise<void> {
    try {
      console.log('[WordSearch] 开始初始化...')
      const startTime = performance.now()

      // 加载词频元数据
      await this.loadWordcountMetadata()

      this.isInitialized = true
      const duration = Math.round(performance.now() - startTime)
      console.log(`[WordSearch] 初始化完成，耗时 ${duration}ms`)
      console.log(`[WordSearch] 索引统计: ${this.stats.totalWords} 词汇`)
    } catch (error) {
      console.error('[WordSearch] 初始化失败:', error)
      throw error
    } finally {
      this.isLoading = false
    }
  }

  // ============ 索引加载 ============

  private async loadWordcountMetadata(): Promise<void> {
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/wordcount_v2/meta.json`)
      if (!response.ok) {
        console.warn('[WordSearch] 无法加载词频元数据')
        return
      }

      const meta = await response.json()
      this.stats.totalWords = meta.total_words || 0
      this.stats.totalChunks = meta.total_chunks || 0

      // 只加载前几个 chunk（高频词汇）
      const chunksToLoad = Math.min(5, this.stats.totalChunks)
      const loadPromises = []
      for (let i = 0; i < chunksToLoad; i++) {
        loadPromises.push(this.loadWordChunk(i))
      }
      await Promise.all(loadPromises)

      // 构建频次排序列表
      this.wordsByFrequency = Array.from(this.words.values())
        .sort((a, b) => b.count - a.count)

    } catch (error) {
      console.warn('[WordSearch] 加载词频元数据失败:', error)
    }
  }

  private async loadWordChunk(chunkIndex: number): Promise<void> {
    try {
      const chunkId = chunkIndex.toString().padStart(4, '0')
      const response = await fetch(`${import.meta.env.BASE_URL}data/wordcount_v2/chunk_${chunkId}.json`)

      if (!response.ok) {
        console.warn(`[WordSearch] 无法加载 wordcount chunk ${chunkIndex}`)
        return
      }

      // 数据格式: [word, count, rank][]
      const rawData: [string, number, number][] = await response.json()

      for (const [word, count, rank] of rawData) {
        const item: WordCountItem = { word, count, rank }
        this.words.set(word, item)

        // 构建长度索引
        const length = word.length
        const existing = this.lengthIndex.get(length) || []
        if (!existing.includes(word)) {
          this.lengthIndex.set(length, [...existing, word])
        }
      }

      this.stats.loadedChunks++
    } catch (error) {
      console.warn(`[WordSearch] 加载 wordcount chunk ${chunkIndex} 失败:`, error)
    }
  }

  // ============ 搜索 API ============

  async search(query: string, options: WordSearchOptions = {}): Promise<WordSearchResult> {
    const startTime = performance.now()
    const { limit = 50, offset = 0, filters } = options

    // 1. 检查缓存
    const cacheKey = this.buildCacheKey(query, options)
    const cached = this.searchCache.get(cacheKey)
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime) }
    }

    // 2. 确保初始化
    await this.initialize()

    // 3. 执行搜索
    let matches: WordCountItem[] = []

    if (query.trim()) {
      // 精确匹配
      const exactMatch = this.words.get(query)
      if (exactMatch) {
        matches = [exactMatch]
      } else {
        // 模糊匹配
        matches = this.fuzzySearch(query)
      }
    } else {
      // 空查询返回所有（按频次排序）
      matches = this.wordsByFrequency
    }

    // 4. 应用过滤器
    if (filters) {
      matches = matches.filter(item => {
        const length = item.word.length
        if (filters.minLength !== undefined && length < filters.minLength) return false
        if (filters.maxLength !== undefined && length > filters.maxLength) return false
        if (filters.minCount !== undefined && item.count < filters.minCount) return false
        if (filters.maxCount !== undefined && item.count > filters.maxCount) return false
        return true
      })
    }

    // 5. 构建结果
    const result: WordSearchResult = {
      items: matches.slice(offset, offset + limit),
      total: matches.length,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }

    // 6. 缓存结果
    this.searchCache.set(cacheKey, result)

    return result
  }

  async searchByLength(length: number, options: WordSearchOptions = {}): Promise<WordSearchResult> {
    const startTime = performance.now()
    const { limit = 50, offset = 0 } = options

    await this.initialize()

    const wordNames = this.lengthIndex.get(length) || []
    const matches: WordCountItem[] = []

    for (const name of wordNames) {
      const word = this.words.get(name)
      if (word) matches.push(word)
    }

    // 按频次排序
    matches.sort((a, b) => b.count - a.count)

    return {
      items: matches.slice(offset, offset + limit),
      total: matches.length,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }
  }

  async getTopWords(topN: number = 100): Promise<WordCountItem[]> {
    await this.initialize()
    return this.wordsByFrequency.slice(0, topN)
  }

  async getWordDetail(word: string): Promise<WordCountItem | null> {
    await this.initialize()
    return this.words.get(word) || null
  }

  // ============ 辅助方法 ============

  private fuzzySearch(query: string): WordCountItem[] {
    const results: WordCountItem[] = []
    const lowerQuery = query.toLowerCase()

    for (const [word, item] of this.words) {
      if (word.includes(query) ||
          word.toLowerCase().includes(lowerQuery)) {
        results.push(item)
      }
    }

    // 按频次排序
    results.sort((a, b) => b.count - a.count)

    return results
  }

  private buildCacheKey(query: string, options: WordSearchOptions): string {
    return `word:${query}:${JSON.stringify(options)}`
  }

  getStats() {
    return {
      ...this.stats,
      wordsCached: this.words.size,
      cacheSize: this.searchCache.size(),
      isInitialized: this.isInitialized
    }
  }

  clearCache(): void {
    this.searchCache.clear()
  }
}

export const wordSearch = WordSearch.getInstance()
export type { WordSearch }
