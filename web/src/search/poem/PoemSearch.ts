import { LRUCache } from '../LRUCache'
import type { PoemSummary } from '@/composables/types'
import { escapeLike, queryRows, queryScalar } from '@/composables/useSQLiteDatabase'

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

interface PoemRow {
  id: string
  title: string
  author: string
  dynasty: string
  genre: string
  chunk_id: number
}

class PoemSearch {
  private static instance: PoemSearch
  private searchCache = new LRUCache<PoemSearchResult>(500, 5 * 60 * 1000)
  private isInitialized = false
  private isLoading = false
  private initPromise: Promise<void> | null = null
  private stats = {
    totalPoems: 0,
    totalKeywords: 0,
    loadedChunks: 1,
    totalChunks: 1
  }

  static getInstance(): PoemSearch {
    if (!PoemSearch.instance) {
      PoemSearch.instance = new PoemSearch()
    }
    return PoemSearch.instance
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return
    if (this.isLoading && this.initPromise) return this.initPromise

    this.isLoading = true
    this.initPromise = (async () => {
      this.stats.totalPoems = Number((await queryScalar<number>('SELECT COUNT(*) AS total FROM poems')) ?? 0)
      this.isInitialized = true
      this.isLoading = false
    })()

    return this.initPromise
  }

  private buildWhere(query: string, filters?: PoemSearchOptions['filters']) {
    const clauses: string[] = []
    const params: Array<string | number> = []

    if (query.trim()) {
      const likeQuery = `%${escapeLike(query.trim())}%`
      clauses.push("(title LIKE ? ESCAPE '\\\\' OR author LIKE ? ESCAPE '\\\\' OR id LIKE ? ESCAPE '\\\\' OR sentences_text LIKE ? ESCAPE '\\\\')")
      params.push(likeQuery, likeQuery, likeQuery, likeQuery)
    }
    if (filters?.dynasty) {
      clauses.push('dynasty = ?')
      params.push(filters.dynasty)
    }
    if (filters?.genre) {
      clauses.push('genre = ?')
      params.push(filters.genre)
    }
    if (filters?.author) {
      clauses.push('author = ?')
      params.push(filters.author)
    }

    return {
      whereSql: clauses.length ? `WHERE ${clauses.join(' AND ')}` : '',
      params
    }
  }

  private mapPoem(row: PoemRow): PoemSummary {
    return {
      id: row.id,
      title: row.title,
      author: row.author,
      dynasty: row.dynasty,
      genre: row.genre,
      chunk_id: row.chunk_id
    }
  }

  async search(query: string, options: PoemSearchOptions = {}): Promise<PoemSearchResult> {
    const startTime = performance.now()
    const { limit = 20, offset = 0, filters } = options
    const cacheKey = JSON.stringify({ query, limit, offset, filters })
    const cached = this.searchCache.get(cacheKey)
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime), source: 'cache' }
    }

    await this.initialize()
    const { whereSql, params } = this.buildWhere(query, filters)
    const total = Number((await queryScalar<number>(`SELECT COUNT(*) AS total FROM poems ${whereSql}`, params)) ?? 0)
    const rows = await queryRows<PoemRow>(
      `SELECT id, title, author, dynasty, genre, chunk_id
       FROM poems
       ${whereSql}
       ORDER BY chunk_id, id
       LIMIT ? OFFSET ?`,
      [...params, limit, offset]
    )

    const result: PoemSearchResult = {
      items: rows.map(row => this.mapPoem(row)),
      total,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }

    this.searchCache.set(cacheKey, result)
    return result
  }

  getStats() {
    return { ...this.stats }
  }

  clearCache() {
    this.searchCache.clear()
  }
}

export const poemSearch = PoemSearch.getInstance()
export { PoemSearch }
