import { LRUCache } from '../LRUCache'
import type { WordCountItem } from '@/composables/types'
import { escapeLike, queryFirst, queryRows, queryScalar } from '@/composables/useSQLiteDatabase'

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

interface WordRow {
  word: string
  count: number
  rank: number
}

function toWord(row: WordRow): WordCountItem {
  return {
    word: row.word,
    count: row.count,
    rank: row.rank
  }
}

class WordSearch {
  private static instance: WordSearch
  private searchCache = new LRUCache<WordSearchResult>(500, 5 * 60 * 1000)
  private isInitialized = false
  private isLoading = false
  private initPromise: Promise<void> | null = null
  private stats = {
    totalWords: 0,
    loadedChunks: 1,
    totalChunks: 1
  }

  static getInstance(): WordSearch {
    if (!WordSearch.instance) {
      WordSearch.instance = new WordSearch()
    }
    return WordSearch.instance
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return
    if (this.isLoading && this.initPromise) return this.initPromise

    this.isLoading = true
    this.initPromise = (async () => {
      this.stats.totalWords = Number((await queryScalar<number>('SELECT COUNT(*) AS total FROM word_counts')) ?? 0)
      this.isInitialized = true
      this.isLoading = false
    })()

    return this.initPromise
  }

  private buildWhere(query: string, filters?: WordSearchOptions['filters']) {
    const clauses: string[] = []
    const params: Array<string | number> = []

    if (query.trim()) {
      clauses.push("word LIKE ? ESCAPE '\\\\'")
      params.push(`%${escapeLike(query.trim())}%`)
    }
    if (filters?.minLength !== undefined) {
      clauses.push('length(word) >= ?')
      params.push(filters.minLength)
    }
    if (filters?.maxLength !== undefined) {
      clauses.push('length(word) <= ?')
      params.push(filters.maxLength)
    }
    if (filters?.minCount !== undefined) {
      clauses.push('count >= ?')
      params.push(filters.minCount)
    }
    if (filters?.maxCount !== undefined) {
      clauses.push('count <= ?')
      params.push(filters.maxCount)
    }

    return {
      whereSql: clauses.length ? `WHERE ${clauses.join(' AND ')}` : '',
      params
    }
  }

  async search(query: string, options: WordSearchOptions = {}): Promise<WordSearchResult> {
    const startTime = performance.now()
    const { limit = 50, offset = 0, filters } = options
    const cacheKey = JSON.stringify({ query, limit, offset, filters })
    const cached = this.searchCache.get(cacheKey)
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime), source: 'cache' }
    }

    await this.initialize()
    const { whereSql, params } = this.buildWhere(query, filters)
    const total = Number((await queryScalar<number>(`SELECT COUNT(*) AS total FROM word_counts ${whereSql}`, params)) ?? 0)
    const rows = await queryRows<WordRow>(
      `SELECT word, count, rank
       FROM word_counts
       ${whereSql}
       ORDER BY count DESC, rank ASC
       LIMIT ? OFFSET ?`,
      [...params, limit, offset]
    )

    const result: WordSearchResult = {
      items: rows.map(toWord),
      total,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }

    this.searchCache.set(cacheKey, result)
    return result
  }

  async searchByLength(length: number, options: WordSearchOptions = {}): Promise<WordSearchResult> {
    return this.search('', {
      ...options,
      filters: {
        ...options.filters,
        minLength: length,
        maxLength: length
      }
    })
  }

  async getTopWords(topN: number = 100): Promise<WordCountItem[]> {
    await this.initialize()
    const rows = await queryRows<WordRow>(
      `SELECT word, count, rank
       FROM word_counts
       ORDER BY count DESC, rank ASC
       LIMIT ?`,
      [topN]
    )
    return rows.map(toWord)
  }

  async getWordDetail(word: string): Promise<WordCountItem | null> {
    await this.initialize()
    const row = await queryFirst<WordRow>(
      `SELECT word, count, rank
       FROM word_counts
       WHERE word = ?`,
      [word]
    )
    return row ? toWord(row) : null
  }

  getStats() {
    return { ...this.stats }
  }

  clearCache() {
    this.searchCache.clear()
  }
}

export const wordSearch = WordSearch.getInstance()
export { WordSearch }
