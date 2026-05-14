import { LRUCache } from '../LRUCache'
import type { AuthorStats } from '@/composables/types'
import { escapeLike, queryRows, queryScalar } from '@/composables/useSQLiteDatabase'

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

interface AuthorRow {
  author: string
  poem_count: number
  poem_ids_json: string
  poem_type_counts_json: string
  meter_patterns_json: string
  word_frequency_json: string
  similar_authors_json: string
}

function parseJson<T>(value: string, fallback: T): T {
  try {
    return value ? JSON.parse(value) as T : fallback
  } catch {
    return fallback
  }
}

function toAuthor(row: AuthorRow): AuthorStats {
  return {
    author: row.author,
    poem_count: row.poem_count,
    poem_ids: parseJson(row.poem_ids_json, [] as string[]),
    poem_type_counts: parseJson(row.poem_type_counts_json, {} as Record<string, number>),
    meter_patterns: parseJson(row.meter_patterns_json, [] as Array<{ pattern: string; count: number }>),
    word_frequency: parseJson(row.word_frequency_json, {} as Record<string, number>),
    similar_authors: parseJson(row.similar_authors_json, [] as Array<{ author: string; similarity: number }>)
  }
}

class AuthorSearch {
  private static instance: AuthorSearch
  private searchCache = new LRUCache<AuthorSearchResult>(200, 5 * 60 * 1000)
  private isInitialized = false
  private isLoading = false
  private initPromise: Promise<void> | null = null
  private stats = {
    totalAuthors: 0,
    loadedChunks: 1,
    totalChunks: 1
  }

  static getInstance(): AuthorSearch {
    if (!AuthorSearch.instance) {
      AuthorSearch.instance = new AuthorSearch()
    }
    return AuthorSearch.instance
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return
    if (this.isLoading && this.initPromise) return this.initPromise

    this.isLoading = true
    this.initPromise = (async () => {
      this.stats.totalAuthors = Number((await queryScalar<number>('SELECT COUNT(*) AS total FROM authors')) ?? 0)
      this.isInitialized = true
      this.isLoading = false
    })()

    return this.initPromise
  }

  async search(query: string, options: AuthorSearchOptions = {}): Promise<AuthorSearchResult> {
    const startTime = performance.now()
    const { limit = 20, offset = 0 } = options
    const cacheKey = JSON.stringify({ query, limit, offset })
    const cached = this.searchCache.get(cacheKey)
    if (cached) {
      return { ...cached, queryTime: Math.round(performance.now() - startTime), source: 'cache' }
    }

    await this.initialize()
    const whereSql = query.trim() ? "WHERE author LIKE ? ESCAPE '\\\\'" : ''
    const params = query.trim() ? [`%${escapeLike(query.trim())}%`] : []
    const total = Number((await queryScalar<number>(`SELECT COUNT(*) AS total FROM authors ${whereSql}`, params)) ?? 0)
    const rows = await queryRows<AuthorRow>(
      `SELECT author, poem_count, poem_ids_json, poem_type_counts_json, meter_patterns_json,
              word_frequency_json, similar_authors_json
       FROM authors
       ${whereSql}
       ORDER BY poem_count DESC, author ASC
       LIMIT ? OFFSET ?`,
      [...params, limit, offset]
    )

    const result: AuthorSearchResult = {
      items: rows.map(toAuthor),
      total,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }

    this.searchCache.set(cacheKey, result)
    return result
  }

  async searchByDynasty(dynasty: string, options: AuthorSearchOptions = {}): Promise<AuthorSearchResult> {
    const startTime = performance.now()
    const { limit = 20, offset = 0 } = options
    await this.initialize()

    const total = Number((await queryScalar<number>(
      `SELECT COUNT(DISTINCT a.author) AS total
       FROM authors a
       JOIN poems p ON p.author = a.author
       WHERE p.dynasty = ?`,
      [dynasty]
    )) ?? 0)

    const rows = await queryRows<AuthorRow>(
      `SELECT a.author, a.poem_count, a.poem_ids_json, a.poem_type_counts_json,
              a.meter_patterns_json, a.word_frequency_json, a.similar_authors_json
       FROM authors a
       JOIN poems p ON p.author = a.author
       WHERE p.dynasty = ?
       GROUP BY a.author
       ORDER BY a.poem_count DESC, a.author ASC
       LIMIT ? OFFSET ?`,
      [dynasty, limit, offset]
    )

    return {
      items: rows.map(toAuthor),
      total,
      queryTime: Math.round(performance.now() - startTime),
      source: 'memory'
    }
  }

  getStats() {
    return { ...this.stats }
  }

  clearCache() {
    this.searchCache.clear()
  }
}

export const authorSearch = AuthorSearch.getInstance()
export { AuthorSearch }
