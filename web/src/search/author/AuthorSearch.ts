/**
 * AuthorSearch - 作者搜索模块
 * 
 * 职责：
 * 1. 从 author_v2 加载作者数据
 * 2. 构建作者名索引
 * 3. 支持按作者名、朝代搜索
 * 4. LRU 缓存搜索结果
 */

import { LRUCache } from '../LRUCache'
import * as flatbuffers from 'flatbuffers'
import type { AuthorStats } from '@/composables/types'
import { AuthorChunkFile } from '@/generated/author-chunk/author-chunk-file'
import { Author } from '@/generated/author-chunk/author'
import { WordFreq } from '@/generated/author-chunk/word-freq'
import { SimilarAuthor } from '@/generated/author-chunk/similar-author'

export interface AuthorSearchResult {
  items: AuthorStats[]
  total: number
  queryTime: number
  source: 'memory' | 'cache'
}

export interface AuthorSearchOptions {
  limit?: number
  offset?: number
}

// 简化版作者数据
interface AuthorData {
  author: string
  poem_count: number
  poem_ids: string[]
  poem_type_counts: Record<string, number>
  word_frequency: Record<string, number>
  similar_authors: Array<{ author: string; similarity: number }>
  dynasty?: string
}

class AuthorSearch {
  private static instance: AuthorSearch

  // 作者数据缓存
  private authors = new Map<string, AuthorData>()
  
  // 朝代索引
  private dynastyIndex = new Map<string, string[]>()
  
  // LRU 缓存
  private searchCache = new LRUCache<AuthorSearchResult>(200, 5 * 60 * 1000)
  
  // 状态
  private isInitialized = false
  private isLoading = false
  private initPromise: Promise<void> | null = null
  
  // 统计
  private stats = {
    totalAuthors: 0,
    loadedChunks: 0,
    totalChunks: 0
  }

  private constructor() {}

  static getInstance(): AuthorSearch {
    if (!AuthorSearch.instance) {
      AuthorSearch.instance = new AuthorSearch()
    }
    return AuthorSearch.instance
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
      console.log('[AuthorSearch] 开始初始化...')
      const startTime = performance.now()
      
      // 加载作者元数据并加载前几个chunk
      await this.loadAuthorData()
      
      this.isInitialized = true
      const duration = Math.round(performance.now() - startTime)
      console.log(`[AuthorSearch] 初始化完成，耗时 ${duration}ms`)
      console.log(`[AuthorSearch] 索引统计: ${this.authors.size} 作者, ${this.dynastyIndex.size} 朝代`)
    } catch (error) {
      console.error('[AuthorSearch] 初始化失败:', error)
      throw error
    } finally {
      this.isLoading = false
    }
  }

  // ============ 索引加载 ============

  private async loadAuthorData(): Promise<void> {
    try {
      // 加载作者元数据
      const response = await fetch(`${import.meta.env.BASE_URL}data/author_v2/authors-meta.json`)
      if (!response.ok) {
        console.warn('[AuthorSearch] 无法加载作者元数据')
        return
      }
      
      const meta = await response.json()
      this.stats.totalAuthors = meta.totalAuthors || 0
      this.stats.totalChunks = meta.total || 0
      
      // 只加载前10个chunk（约前1000个热门作者）
      const chunksToLoad = Math.min(10, this.stats.totalChunks)
      const loadPromises = []
      for (let i = 0; i < chunksToLoad; i++) {
        loadPromises.push(this.loadAuthorChunk(i))
      }
      await Promise.all(loadPromises)
      
    } catch (error) {
      console.warn('[AuthorSearch] 加载作者数据失败:', error)
    }
  }

  private async loadAuthorChunk(chunkIndex: number): Promise<void> {
    try {
      const chunkId = chunkIndex.toString().padStart(4, '0')
      const filePath = `author_v2/author_chunk_${chunkId}.fbs`
      
      const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
      if (!response.ok) {
        console.warn(`[AuthorSearch] 无法加载作者chunk ${chunkIndex}`)
        return
      }

      const buffer = new Uint8Array(await response.arrayBuffer())
      const bb = new flatbuffers.ByteBuffer(buffer)
      const chunkFile = AuthorChunkFile.getRootAsAuthorChunkFile(bb)
      
      const len = chunkFile.authorsLength()
      for (let i = 0; i < len; i++) {
        const author = chunkFile.authors(i)
        if (author) {
          this.addAuthorToIndex(author)
        }
      }
      
      this.stats.loadedChunks++
    } catch (error) {
      console.warn(`[AuthorSearch] 加载作者chunk ${chunkIndex} 失败:`, error)
    }
  }

  private addAuthorToIndex(author: Author): void {
    const authorName = author.author() || ''
    if (!authorName) return

    // 提取词频数据
    const wordFrequency: Record<string, number> = {}
    const wordFreqLen = author.wordFrequencyLength()
    for (let i = 0; i < wordFreqLen && i < 10; i++) {  // 只取前10个高频词
      const wf = author.wordFrequency(i)
      if (wf) {
        const word = wf.word()
        if (word) {
          wordFrequency[word] = wf.count()
        }
      }
    }

    // 提取相似作者
    const similarAuthors: Array<{ author: string; similarity: number }> = []
    const similarLen = author.similarAuthorsLength()
    for (let i = 0; i < similarLen && i < 5; i++) {  // 只取前5个相似作者
      const sa = author.similarAuthors(i)
      if (sa) {
        const name = sa.author()
        if (name) {
          similarAuthors.push({ author: name, similarity: sa.similarity() })
        }
      }
    }

    // 提取诗词类型统计
    const poemTypeCounts: Record<string, number> = {}
    const typeCountsLen = author.poemTypeCountsLength()
    for (let i = 0; i < typeCountsLen; i++) {
      const tc = author.poemTypeCounts(i)
      if (tc) {
        const typeName = tc.word()
        if (typeName) {
          poemTypeCounts[typeName] = tc.count()
        }
      }
    }

    // 推断朝代（根据诗词类型或作者名特征）
    let dynasty: string | undefined
    if (poemTypeCounts['唐诗'] || poemTypeCounts['唐']) {
      dynasty = '唐'
    } else if (poemTypeCounts['宋词'] || poemTypeCounts['宋']) {
      dynasty = '宋'
    } else if (poemTypeCounts['元曲'] || poemTypeCounts['元']) {
      dynasty = '元'
    }

    const authorData: AuthorData = {
      author: authorName,
      poem_count: author.poemCount(),
      poem_ids: [],
      poem_type_counts: poemTypeCounts,
      word_frequency: wordFrequency,
      similar_authors: similarAuthors,
      dynasty
    }

    this.authors.set(authorName, authorData)

    // 构建朝代索引
    if (dynasty) {
      const existing = this.dynastyIndex.get(dynasty) || []
      if (!existing.includes(authorName)) {
        this.dynastyIndex.set(dynasty, [...existing, authorName])
      }
    }
  }

  // ============ 搜索 API ============

  async search(query: string, options: AuthorSearchOptions = {}): Promise<AuthorSearchResult> {
    const startTime = performance.now()
    const { limit = 20, offset = 0 } = options
    
    // 1. 检查缓存
    const cacheKey = this.buildCacheKey(query, options)
    const cached = this.searchCache.get(cacheKey)
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime) }
    }
    
    // 2. 确保初始化
    await this.initialize()
    
    // 3. 执行搜索
    const matches: AuthorData[] = []
    const lowerQuery = query.toLowerCase()
    
    for (const [name, author] of this.authors) {
      // 精确匹配或包含匹配
      if (name === query || 
          name.includes(query) || 
          name.toLowerCase().includes(lowerQuery)) {
        matches.push(author)
      }
    }
    
    // 按诗词数量排序
    matches.sort((a, b) => b.poem_count - a.poem_count)
    
    // 4. 构建结果
    const result: AuthorSearchResult = {
      items: matches.slice(offset, offset + limit).map(this.convertToAuthorStats),
      total: matches.length,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }
    
    // 5. 缓存结果
    this.searchCache.set(cacheKey, result)
    
    return result
  }

  async searchByDynasty(dynasty: string, options: AuthorSearchOptions = {}): Promise<AuthorSearchResult> {
    const startTime = performance.now()
    const { limit = 20, offset = 0 } = options
    
    await this.initialize()
    
    const authorNames = this.dynastyIndex.get(dynasty) || []
    const matches: AuthorData[] = []
    
    for (const name of authorNames) {
      const author = this.authors.get(name)
      if (author) matches.push(author)
    }
    
    // 按诗词数量排序
    matches.sort((a, b) => b.poem_count - a.poem_count)
    
    return {
      items: matches.slice(offset, offset + limit).map(this.convertToAuthorStats),
      total: matches.length,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }
  }

  // ============ 辅助方法 ============

  private convertToAuthorStats(data: AuthorData): AuthorStats {
    return {
      author: data.author,
      poem_count: data.poem_count,
      poem_ids: data.poem_ids,
      poem_type_counts: data.poem_type_counts,
      word_frequency: data.word_frequency,
      similar_authors: data.similar_authors,
      meter_patterns: []
    }
  }

  private buildCacheKey(query: string, options: AuthorSearchOptions): string {
    return `author:${query}:${JSON.stringify(options)}`
  }

  getStats() {
    return {
      ...this.stats,
      authorsCached: this.authors.size,
      cacheSize: this.searchCache.size(),
      isInitialized: this.isInitialized
    }
  }

  clearCache(): void {
    this.searchCache.clear()
  }
}

export const authorSearch = AuthorSearch.getInstance()
export type { AuthorSearch }
