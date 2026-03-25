/**
 * @overview
 * file: web/src/composables/types.ts
 * category: pipeline
 * tech: TypeScript
 * solved: 封装数据加载与状态编排（关键函数：load/query/update）
 * data_source: 组合式状态与组件内部状态
 * data_flow: 参数输入 -> 读取缓存/远端 -> 数据校验与归一化 -> 输出响应式状态
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 核心导出: PoemSummary, PoemDetail, PoemFilter
 */
export interface PoemSummary {
  id: string
  title: string
  author: string
  dynasty: string
  genre: string
  chunk_id?: number  // 诗词所在的 chunk 编号，用于快速定位
}

export interface PoemDetail extends PoemSummary {
  poem_type?: string
  meter_pattern?: string
  sentences: string[]
  words: string[]
  hash: string
}

export interface PoemFilter {
  dynasty?: string
  genre?: string
  author?: string
  title?: string
  search?: string
}

export interface PoemChunkMeta {
  id: number
  file: string
  count: number
  dynasties: string[]
  genres: string[]
}

export interface PoemsIndexMeta {
  total: number
  chunks: number
  generatedAt: string
}

export interface PoemsIndexStats {
  dynasties: string[]
  genres: string[]
  counts: {
    songshi: number
    songci: number
    tangshi: number
  }
}

export interface PoemsIndex {
  metadata: PoemsIndexMeta
  stats: PoemsIndexStats
  chunks: PoemChunkMeta[]
}

export interface PoemQueryResult {
  poems: PoemSummary[]
  total: number
  filteredTotal: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface AuthorStats {
  author: string
  poem_count: number
  poem_ids: string[]
  poem_type_counts: Record<string, number>
  meter_patterns: Array<{ pattern: string; count: number }>
  word_frequency: Record<string, number>
  similar_authors: Array<{ author: string; similarity: number }>
}

export interface AuthorChunkMeta {
  index: number
  filename: string
  authorCount: number
}

export interface AuthorsIndex {
  total: number
  totalAuthors: number
  chunks: AuthorChunkMeta[]
}

export interface AuthorFilter {
  dynasty?: string
  minPoems?: number
  maxPoems?: number
  search?: string
}

export interface AuthorQueryResult {
  authors: AuthorStats[]
  total: number
  filteredTotal: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface WordCountItem {
  word: string
  count: number
  rank: number
}

export interface WordCountChunkMeta {
  file: string
  index: number
  start_rank: number
  end_rank: number
  count: number
  start_word: string
  end_word: string
  total_count: number
}

export interface WordCountMeta {
  version: string
  format: string
  total_words: number
  total_chunks: number
  chunks: WordCountChunkMeta[]
}

export interface WordCountQueryResult {
  words: WordCountItem[]
  total: number
  startRank: number
  endRank: number
}

export interface WordSimilarityData {
  word: string
  /** FastText 内部索引值，非真实词频 */
  frequency: number
  similarWords: Array<{
    word: string
    similarity: number
  }>
}

export interface SimilarWordResult {
  word: string
  similarity: number
  /** FastText 内部索引值，非真实词频 */
  frequency: number
}

export interface WordSimilarityMetadata {
  total_words: number
  total_chunks: number
  vocab_size: number
  similarity_threshold: number
}

export interface SearchResult {
  id: string
  title: string
  author: string
  dynasty: string
  score: number
}

export interface SearchOptions {
  query: string
  dynasty?: string
  genre?: string
  page?: number
  pageSize?: number
}

export interface SearchResultSet {
  results: SearchResult[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface PoemIndexManifest {
  metadata: {
    total: number
    chunks: number
    indexFiles: number
    prefixLength: number
    generatedAt: string
  }
  prefixMap: Record<string, string>
}
