/**
 * @overview
 * file: web/src/search/poem/PoemSearch.ts
 * category: algorithm
 * tech: TypeScript
 * solved: 实现检索与索引策略（核心导出：poemSearch, PoemSearchResult, PoemSearchOptions）
 * data_source: public/data 静态分块文件
 * data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
 * complexity: 常见查询/筛选 O(n)，排序 O(n log n)，空间复杂度常见 O(n)
 * unique: 核心导出: poemSearch, PoemSearchResult, PoemSearchOptions
 */
/**
 * PoemSearch - 诗词搜索模块
 * 
 * 职责：
 * 1. 加载 keyword_index 构建倒排索引
 * 2. 缓存诗词摘要数据用于搜索展示
 * 3. 支持关键词、标题、作者、朝代、体裁搜索
 * 4. LRU 缓存搜索结果
 */

import { LRUCache } from '../LRUCache'
import type { PoemSummary, PoemFilter } from '@/composables/types'

export interface PoemSearchResult {
  items: PoemSummary[]
  total: number
  queryTime: number
  source: 'memory' | 'cache'
}

export interface PoemSearchOptions {
  limit?: number
  offset?: number
  filters?: {
    dynasty?: string
    genre?: string
    author?: string
  }
}

class PoemSearch {
  private static instance: PoemSearch

  // 倒排索引: 关键词 -> 诗词ID列表
  private keywordIndex = new Map<string, string[]>()
  
  // 辅助索引
  private authorIndex = new Map<string, string[]>()   // 作者 -> 诗词ID
  private dynastyIndex = new Map<string, string[]>()  // 朝代 -> 诗词ID
  private genreIndex = new Map<string, string[]>()    // 体裁 -> 诗词ID
  
  // 诗词数据缓存
  private poems = new Map<string, PoemSummary>()
  
  // LRU 缓存
  private searchCache = new LRUCache<PoemSearchResult>(500, 5 * 60 * 1000) // 5分钟TTL
  
  // 状态
  private isInitialized = false
  private isLoading = false
  private initPromise: Promise<void> | null = null
  
  // 统计
  private stats = {
    totalKeywords: 0,
    loadedChunks: 0,
    totalChunks: 13
  }

  private constructor() {}

  static getInstance(): PoemSearch {
    if (!PoemSearch.instance) {
      PoemSearch.instance = new PoemSearch()
    }
    return PoemSearch.instance
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
      console.log('[PoemSearch] 开始初始化...')
      const startTime = performance.now()
      
      // 并行加载索引
      await Promise.all([
        this.loadKeywordIndex(),
        this.loadPoemManifest()
      ])
      
      this.isInitialized = true
      const duration = Math.round(performance.now() - startTime)
      console.log(`[PoemSearch] 初始化完成，耗时 ${duration}ms`)
      console.log(`[PoemSearch] 索引统计: ${this.stats.totalKeywords} 关键词, ${this.poems.size} 诗词缓存`)
    } catch (error) {
      console.error('[PoemSearch] 初始化失败:', error)
      throw error
    } finally {
      this.isLoading = false
    }
  }

  // ============ 索引加载 ============

  private async loadKeywordIndex(): Promise<void> {
    const loadPromises = []
    for (let i = 0; i < this.stats.totalChunks; i++) {
      loadPromises.push(this.loadKeywordChunk(i))
    }
    await Promise.all(loadPromises)
  }

  private async loadKeywordChunk(chunkIndex: number): Promise<void> {
    try {
      const chunkId = chunkIndex.toString().padStart(4, '0')
      const response = await fetch(`${import.meta.env.BASE_URL}data/keyword_index/keyword_${chunkId}.json`)
      
      if (!response.ok) {
        console.warn(`[PoemSearch] 无法加载 keyword chunk ${chunkIndex}`)
        return
      }
      
      const data: Record<string, string[]> = await response.json()
      
      for (const [keyword, poemIds] of Object.entries(data)) {
        // 合并相同关键词的诗词ID
        const existing = this.keywordIndex.get(keyword) || []
        this.keywordIndex.set(keyword, [...new Set([...existing, ...poemIds])])
        this.stats.totalKeywords++
      }
      
      this.stats.loadedChunks++
    } catch (error) {
      console.warn(`[PoemSearch] 加载 keyword chunk ${chunkIndex} 失败:`, error)
    }
  }

  private async loadPoemManifest(): Promise<void> {
    // 加载诗词清单的前几个 chunk 作为热数据
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/poem_index/poem_index_manifest.json`)
      if (!response.ok) return
      
      const manifest = await response.json()
      const prefixes = Object.keys(manifest.prefixMap).slice(0, 20) // 只加载前20个
      
      await Promise.all(
        prefixes.map(prefix => this.loadPoemChunk(manifest.prefixMap[prefix]))
      )
    } catch (error) {
      console.warn('[PoemSearch] 加载 poem manifest 失败:', error)
    }
  }

  private async loadPoemChunk(filename: string): Promise<void> {
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/poem_index/${filename}`)
      if (!response.ok) return
      
      const data: Record<string, PoemSummary> = await response.json()
      
      for (const [id, poem] of Object.entries(data)) {
        this.poems.set(id, poem)
        
        // 构建辅助索引
        this.addToIndex(this.authorIndex, poem.author, id)
        this.addToIndex(this.dynastyIndex, poem.dynasty, id)
        this.addToIndex(this.genreIndex, poem.genre, id)
      }
    } catch (error) {
      console.warn(`[PoemSearch] 加载 poem chunk 失败:`, error)
    }
  }

  private addToIndex(index: Map<string, string[]>, key: string, id: string): void {
    const existing = index.get(key) || []
    if (!existing.includes(id)) {
      index.set(key, [...existing, id])
    }
  }

  // ============ 搜索 API ============

  async search(query: string, options: PoemSearchOptions = {}): Promise<PoemSearchResult> {
    const startTime = performance.now()
    const { limit = 20, offset = 0, filters } = options
    
    // 1. 检查缓存
    const cacheKey = this.buildCacheKey(query, options)
    const cached = this.searchCache.get(cacheKey)
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime) }
    }
    
    // 2. 确保初始化
    await this.initialize()
    
    // 3. 执行搜索
    let poemIds: string[] = []
    const hasQuery = query.trim().length > 0
    const hasFilters = filters?.dynasty || filters?.genre || filters?.author
    
    if (hasQuery) {
      // 3.1 关键词精确匹配 (O(1))
      if (this.keywordIndex.has(query)) {
        poemIds = this.keywordIndex.get(query)!
      }
      
      // 3.2 如果没有关键词匹配，搜索标题和作者
      if (poemIds.length === 0) {
        poemIds = this.fuzzySearch(query)
      }
    } else if (hasFilters) {
      // 3.3 无关键词但有过滤器时，从过滤器对应的索引开始
      // 优先使用范围最小的索引作为基础集合
      const indexSizes: Array<{ type: string; ids: string[]; size: number }> = []
      
      if (filters?.author) {
        const ids = this.authorIndex.get(filters.author) || []
        indexSizes.push({ type: 'author', ids, size: ids.length })
      }
      if (filters?.dynasty) {
        const ids = this.dynastyIndex.get(filters.dynasty) || []
        indexSizes.push({ type: 'dynasty', ids, size: ids.length })
      }
      if (filters?.genre) {
        const ids = this.genreIndex.get(filters.genre) || []
        indexSizes.push({ type: 'genre', ids, size: ids.length })
      }
      
      // 使用最小的索引作为基础，减少后续交集运算量
      indexSizes.sort((a, b) => a.size - b.size)
      if (indexSizes.length > 0) {
        poemIds = indexSizes[0]!.ids
      }
    } else {
      // 3.4 既无关键词也无过滤器，返回所有诗词
      poemIds = Array.from(this.poems.keys())
    }
    
    // 3.5 应用过滤器（当有过滤器时，与查询结果取交集）
    let filteredIds = poemIds
    if (filters?.dynasty) {
      filteredIds = this.intersect(filteredIds, this.dynastyIndex.get(filters.dynasty) || [])
    }
    if (filters?.genre) {
      filteredIds = this.intersect(filteredIds, this.genreIndex.get(filters.genre) || [])
    }
    if (filters?.author) {
      filteredIds = this.intersect(filteredIds, this.authorIndex.get(filters.author) || [])
    }
    
    // 4. 获取诗词详情
    const items: PoemSummary[] = []
    for (let i = offset; i < Math.min(offset + limit, filteredIds.length); i++) {
      const id = filteredIds[i]
      if (!id) continue
      
      // 先从内存缓存获取
      let poem = this.poems.get(id)
      
      // 如果没有，尝试从 usePoemsV2 加载（这里简化处理）
      if (!poem) {
        poem = await this.loadPoemById(id)
      }
      
      if (poem) items.push(poem)
    }
    
    // 5. 构建结果
    const result: PoemSearchResult = {
      items,
      total: filteredIds.length,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }
    
    // 6. 缓存结果
    this.searchCache.set(cacheKey, result)
    
    return result
  }

  private fuzzySearch(query: string): string[] {
    const results: string[] = []
    const lowerQuery = query.toLowerCase()
    
    for (const [id, poem] of this.poems) {
      if (poem.title.includes(query) || 
          poem.author.includes(query) ||
          poem.title.toLowerCase().includes(lowerQuery) ||
          poem.author.toLowerCase().includes(lowerQuery)) {
        results.push(id)
      }
    }
    
    return results
  }

  private intersect(a: string[], b: string[]): string[] {
    const setB = new Set(b)
    return a.filter(id => setB.has(id))
  }

  private async loadPoemById(id: string): Promise<PoemSummary | undefined> {
    // 简化实现：从 poem_index 加载
    // 实际应该调用 usePoemsV2 的方法
    return undefined
  }

  // ============ 辅助方法 ============

  private buildCacheKey(query: string, options: PoemSearchOptions): string {
    return `poem:${query}:${JSON.stringify(options)}`
  }

  getStats() {
    return {
      ...this.stats,
      poemsCached: this.poems.size,
      cacheSize: this.searchCache.size(),
      isInitialized: this.isInitialized
    }
  }

  clearCache(): void {
    this.searchCache.clear()
  }
}

export const poemSearch = PoemSearch.getInstance()
export type { PoemSearch }
