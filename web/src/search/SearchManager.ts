/**
 * SearchManager - 统一搜索管理器
 *
 * 功能：
 * 1. 关键词倒排索引 - O(1) 查找包含关键词的诗词
 * 2. 作者索引 - 快速查找诗人
 * 3. 词频索引 - 快速查找词汇
 * 4. LRU 缓存 - 缓存搜索结果
 * 5. 智能预加载 - 预测用户行为预加载数据
 */

import { LRUCache } from './LRUCache'
import type { PoemSummary, AuthorStats, WordCountItem } from '@/composables/types'
import { getVerifiedChunk } from '@/composables/useVerifiedCache'

// 搜索结果类型
export interface SearchResult<T> {
  items: T[]
  total: number
  source: 'memory' | 'cache' | 'indexeddb' | 'network'
  queryTime: number
}

// 搜索选项
export interface SearchOptions {
  limit?: number
  offset?: number
  filters?: {
    dynasty?: string
    genre?: string
    author?: string
  }
}

// 索引条目
interface IndexEntry {
  poemIds: Set<string>
  authors: Set<string>
  words: Set<string>
}

class SearchManager {
  private static instance: SearchManager
  
  // 内存索引
  private keywordIndex = new Map<string, Set<string>>()  // 关键词 -> 诗词ID
  private authorIndex = new Map<string, Set<string>>()   // 作者 -> 诗词ID
  private dynastyIndex = new Map<string, Set<string>>()  // 朝代 -> 诗词ID
  private genreIndex = new Map<string, Set<string>>()    // 体裁 -> 诗词ID
  
  // 数据存储
  private poems = new Map<string, PoemSummary>()
  private authors = new Map<string, AuthorStats>()
  private words = new Map<string, WordCountItem>()
  
  // LRU 缓存
  private searchCache = new LRUCache<SearchResult<unknown>>(1000, 5 * 60 * 1000) // 5分钟TTL
  private poemCache = new LRUCache<PoemSummary>(1000)
  private authorCache = new LRUCache<AuthorStats>(100)
  
  // 状态
  private isInitialized = false
  private isLoading = false
  private initPromise: Promise<void> | null = null
  
  // 元数据
  private totalKeywords = 0
  private loadedChunks = 0
  private totalChunks = 13 // keyword_index 有 13 个 chunk

  private constructor() {}

  static getInstance(): SearchManager {
    if (!SearchManager.instance) {
      SearchManager.instance = new SearchManager()
    }
    return SearchManager.instance
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
      console.log('[SearchManager] 开始初始化...')
      const startTime = performance.now()
      
      // 并行加载所有索引
      await Promise.all([
        this.loadKeywordIndex(),
        this.loadPoemIndex(),
        this.loadAuthorIndex()
      ])
      
      this.isInitialized = true
      const duration = Math.round(performance.now() - startTime)
      console.log(`[SearchManager] 初始化完成，耗时 ${duration}ms`)
      console.log(`[SearchManager] 索引统计: ${this.totalKeywords} 关键词, ${this.poems.size} 诗词, ${this.authors.size} 诗人`)
    } catch (error) {
      console.error('[SearchManager] 初始化失败:', error)
      throw error
    } finally {
      this.isLoading = false
    }
  }

  // ============ 索引加载 ============

  private async loadKeywordIndex(): Promise<void> {
    // 加载 keyword_index (13 个文件)
    const loadPromises = []
    for (let i = 0; i < this.totalChunks; i++) {
      loadPromises.push(this.loadKeywordChunk(i))
    }
    
    await Promise.all(loadPromises)
  }

  private async loadKeywordChunk(chunkIndex: number): Promise<void> {
    try {
      const chunkId = chunkIndex.toString().padStart(4, '0')
      const filePath = `keyword_index/keyword_${chunkId}.json`

      const result = await getVerifiedChunk<Record<string, string[]>>(
        'search-manager',
        chunkIndex,
        filePath,
        async () => {
          const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
          if (!response.ok) {
            throw new Error(`Failed to load keyword chunk ${chunkIndex}`)
          }
          return response.json()
        }
      )

      if (!result.data) {
        console.warn(`[SearchManager] 无法加载 keyword chunk ${chunkIndex}: ${result.error || 'Unknown error'}`)
        return
      }

      // 构建倒排索引
      for (const [keyword, poemIds] of Object.entries(result.data)) {
        if (!this.keywordIndex.has(keyword)) {
          this.keywordIndex.set(keyword, new Set())
          this.totalKeywords++
        }
        const set = this.keywordIndex.get(keyword)!
        poemIds.forEach(id => set.add(id))
      }

      this.loadedChunks++
    } catch (error) {
      console.warn(`[SearchManager] 加载 keyword chunk ${chunkIndex} 失败:`, error)
    }
  }

  private async loadPoemIndex(): Promise<void> {
    // 加载诗词清单，用于获取基本信息
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/poem_index/poem_index_manifest.json`)
      if (!response.ok) return
      
      const manifest = await response.json()
      
      // 只加载前几个 chunk 作为热数据
      const hotPrefixes = Object.keys(manifest.prefixMap).slice(0, 10)
      await Promise.all(
        hotPrefixes.map(prefix => this.loadPoemChunk(manifest.prefixMap[prefix]))
      )
    } catch (error) {
      console.warn('[SearchManager] 加载 poem index 失败:', error)
    }
  }

  private async loadPoemChunk(filename: string): Promise<void> {
    try {
      const filePath = `poem_index/${filename}`

      const result = await getVerifiedChunk<Record<string, PoemSummary>>(
        'search-manager',
        filename.replace('.json', ''),
        filePath,
        async () => {
          const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
          if (!response.ok) {
            throw new Error(`Failed to load poem chunk ${filename}`)
          }
          return response.json()
        }
      )

      if (!result.data) {
        console.warn(`[SearchManager] 无法加载 poem chunk ${filename}: ${result.error || 'Unknown error'}`)
        return
      }

      for (const [id, poem] of Object.entries(result.data)) {
        this.poems.set(id, poem)

        // 构建辅助索引
        if (!this.authorIndex.has(poem.author)) {
          this.authorIndex.set(poem.author, new Set())
        }
        this.authorIndex.get(poem.author)!.add(id)

        if (!this.dynastyIndex.has(poem.dynasty)) {
          this.dynastyIndex.set(poem.dynasty, new Set())
        }
        this.dynastyIndex.get(poem.dynasty)!.add(id)

        if (!this.genreIndex.has(poem.genre)) {
          this.genreIndex.set(poem.genre, new Set())
        }
        this.genreIndex.get(poem.genre)!.add(id)
      }
    } catch (error) {
      console.warn(`[SearchManager] 加载 poem chunk 失败:`, error)
    }
  }

  private async loadAuthorIndex(): Promise<void> {
    // 加载作者元数据
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/author_v2/authors-meta.json`)
      if (!response.ok) return
      
      const meta = await response.json()
      
      // 只加载热门作者 (前 50)
      const hotChunks = meta.chunks.slice(0, 50)
      await Promise.all(
        hotChunks.map((chunk: { index: number }) => this.loadAuthorChunk(chunk.index))
      )
    } catch (error) {
      console.warn('[SearchManager] 加载 author index 失败:', error)
    }
  }

  private async loadAuthorChunk(chunkIndex: number): Promise<void> {
    // 这里简化处理，实际需要解析 FlatBuffers
    // 暂时跳过，等需要时再加载
  }

  // ============ 搜索 API ============

  /**
   * 搜索诗词 - 核心方法
   */
  async searchPoems(
    query: string, 
    options: SearchOptions = {}
  ): Promise<SearchResult<PoemSummary>> {
    const startTime = performance.now()
    const { limit = 20, offset = 0, filters } = options
    
    // 1. 检查缓存
    const cacheKey = this.buildCacheKey('poem', query, options)
    const cached = this.searchCache.get(cacheKey) as SearchResult<PoemSummary> | undefined
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime) }
    }
    
    // 2. 确保初始化
    await this.initialize()
    
    // 3. 执行搜索
    let poemIds: Set<string> = new Set()
    let source: SearchResult<PoemSummary>['source'] = 'memory'
    const hasQuery = query.trim().length > 0
    const hasFilters = filters?.dynasty || filters?.genre || filters?.author
    
    if (hasQuery) {
      // 3.1 关键词匹配 (O(1))
      if (this.keywordIndex.has(query)) {
        poemIds = new Set(this.keywordIndex.get(query)!)
      }
      
      // 3.2 标题/作者模糊匹配
      if (poemIds.size === 0) {
        for (const [id, poem] of this.poems) {
          if (poem.title.includes(query) || poem.author.includes(query)) {
            poemIds.add(id)
          }
        }
        source = 'memory'
      }
    } else if (hasFilters) {
      // 3.3 无关键词但有过滤器时，从过滤器对应的索引开始
      // 优先使用范围最小的索引作为基础集合
      const indexSizes: Array<{ type: string; ids: Set<string>; size: number }> = []
      
      if (filters?.author) {
        const ids = this.authorIndex.get(filters.author) || new Set()
        indexSizes.push({ type: 'author', ids, size: ids.size })
      }
      if (filters?.dynasty) {
        const ids = this.dynastyIndex.get(filters.dynasty) || new Set()
        indexSizes.push({ type: 'dynasty', ids, size: ids.size })
      }
      if (filters?.genre) {
        const ids = this.genreIndex.get(filters.genre) || new Set()
        indexSizes.push({ type: 'genre', ids, size: ids.size })
      }
      
      // 使用最小的索引作为基础，减少后续过滤运算量
      indexSizes.sort((a, b) => a.size - b.size)
      if (indexSizes.length > 0) {
        poemIds = indexSizes[0]!.ids
      }
      source = 'memory'
    } else {
      // 3.4 既无关键词也无过滤器，返回所有诗词
      poemIds = new Set(this.poems.keys())
      source = 'memory'
    }
    
    // 3.5 应用过滤器（当有过滤器时，与查询结果取交集）
    let filteredIds = Array.from(poemIds)
    if (filters?.dynasty) {
      const dynastyIds = this.dynastyIndex.get(filters.dynasty) || new Set()
      filteredIds = filteredIds.filter(id => dynastyIds.has(id))
    }
    if (filters?.genre) {
      const genreIds = this.genreIndex.get(filters.genre) || new Set()
      filteredIds = filteredIds.filter(id => genreIds.has(id))
    }
    if (filters?.author) {
      const authorIds = this.authorIndex.get(filters.author) || new Set()
      filteredIds = filteredIds.filter(id => authorIds.has(id))
    }
    
    // 4. 获取诗词详情
    const items: PoemSummary[] = []
    for (let i = offset; i < Math.min(offset + limit, filteredIds.length); i++) {
      const id = filteredIds[i]
      if (!id) continue
      const poem = this.getPoemById(id)
      if (poem) items.push(poem)
    }
    
    // 5. 构建结果
    const result: SearchResult<PoemSummary> = {
      items,
      total: filteredIds.length,
      source,
      queryTime: Math.round(performance.now() - startTime)
    }
    
    // 6. 缓存结果
    this.searchCache.set(cacheKey, result)
    
    return result
  }

  /**
   * 搜索作者
   */
  async searchAuthors(
    query: string,
    options: SearchOptions = {}
  ): Promise<SearchResult<AuthorStats>> {
    const startTime = performance.now()
    const { limit = 20, offset = 0 } = options
    
    // 检查缓存
    const cacheKey = this.buildCacheKey('author', query, options)
    const cached = this.searchCache.get(cacheKey) as SearchResult<AuthorStats> | undefined
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime) }
    }
    
    await this.initialize()
    
    // 作者名匹配
    const matches: AuthorStats[] = []
    for (const [name, author] of this.authors) {
      if (name.includes(query) || query.includes(name)) {
        matches.push(author)
      }
    }
    
    const result: SearchResult<AuthorStats> = {
      items: matches.slice(offset, offset + limit),
      total: matches.length,
      source: 'memory',
      queryTime: Math.round(performance.now() - startTime)
    }
    
    this.searchCache.set(cacheKey, result)
    return result
  }

  /**
   * 搜索词汇
   */
  async searchWords(
    query: string,
    options: SearchOptions = {}
  ): Promise<SearchResult<WordCountItem>> {
    const startTime = performance.now()
    const { limit = 50, offset = 0 } = options
    
    // 检查缓存
    const cacheKey = this.buildCacheKey('word', query, options)
    const cached = this.searchCache.get(cacheKey) as SearchResult<WordCountItem> | undefined
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime) }
    }
    
    await this.initialize()
    
    // 词汇匹配
    const matches: WordCountItem[] = []
    for (const [word, item] of this.words) {
      if (word.includes(query) || query.includes(word)) {
        matches.push(item)
      }
    }
    
    // 按频次排序
    matches.sort((a, b) => b.count - a.count)
    
    const result: SearchResult<WordCountItem> = {
      items: matches.slice(offset, offset + limit),
      total: matches.length,
      source: 'memory',
      queryTime: Math.round(performance.now() - startTime)
    }
    
    this.searchCache.set(cacheKey, result)
    return result
  }

  /**
   * 通过 ID 获取诗词
   */
  getPoemById(id: string): PoemSummary | undefined {
    // 1. 检查内存缓存
    const cached = this.poemCache.get(id)
    if (cached) return cached
    
    // 2. 检查内存存储
    const poem = this.poems.get(id)
    if (poem) {
      this.poemCache.set(id, poem)
      return poem
    }
    
    return undefined
  }

  /**
   * 通过名字获取作者
   */
  getAuthorByName(name: string): AuthorStats | undefined {
    const cached = this.authorCache.get(name)
    if (cached) return cached
    
    const author = this.authors.get(name)
    if (author) {
      this.authorCache.set(name, author)
      return author
    }
    
    return undefined
  }

  /**
   * 获取热门诗词
   */
  async getHotPoems(limit = 10): Promise<PoemSummary[]> {
    // 返回已加载的前 N 首
    return Array.from(this.poems.values()).slice(0, limit)
  }

  /**
   * 获取热门作者
   */
  async getHotAuthors(limit = 10): Promise<AuthorStats[]> {
    const authors = Array.from(this.authors.values())
    authors.sort((a, b) => b.poem_count - a.poem_count)
    return authors.slice(0, limit)
  }

  // ============ 辅助方法 ============

  private buildCacheKey(type: string, query: string, options: SearchOptions): string {
    return `${type}:${query}:${JSON.stringify(options)}`
  }

  /**
   * 预加载数据
   */
  async preload(query: string): Promise<void> {
    // 预加载相关数据
    requestIdleCallback(async () => {
      await this.searchPoems(query, { limit: 5 })
    })
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      keywords: this.totalKeywords,
      poems: this.poems.size,
      authors: this.authors.size,
      words: this.words.size,
      cacheSize: this.searchCache.size(),
      isInitialized: this.isInitialized,
      loadedChunks: this.loadedChunks,
      totalChunks: this.totalChunks
    }
  }

  /**
   * 清空缓存
   */
  clearCache(): void {
    this.searchCache.clear()
    this.poemCache.clear()
    this.authorCache.clear()
  }
}

// 导出单例
export const searchManager = SearchManager.getInstance()

// 导出类型
export type { SearchManager }
