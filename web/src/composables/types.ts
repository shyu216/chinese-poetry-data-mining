/**
 * @overview
 * file: web/src/composables/types.ts
 * category: types
 * tech: TypeScript
 * summary: 全局 TypeScript 接口与类型定义，供 composables、views 和组件共享。
 *
 * Data pipeline (概念性):
 *  - 此文件仅声明类型，不直接执行数据加载或网络请求。
 *  - 其他模块遵循这些类型进行数据解析、缓存与展示（例如：poem/chunk 元数据、作者统计、词频、相似词）
 *
 * Complexity & cost:
 *  - 类型声明本身无运行时开销；但对应的运行时数据结构（数组、映射）在使用时会产生 O(n) 的遍历/筛选成本。
 *  - 设计良好的索引（Map/前缀分片）可把常见查询从 O(n) 降到 O(1)~O(log n)。
 *
 * Exports / responsibilities:
 *  - 导出诗词、作者、词频、相似词、检索返回等核心类型，作为项目的契约（PoemSummary, PoemDetail, PoemsIndex, AuthorStats, WordCountMeta 等）。
 *
 * Potential issues & recommendations:
 *  - 保持类型与后端/构建产物（预处理脚本生成的 JSON/FlatBuffers）同步，避免运行时断言失败。
 *  - 避免在类型文件中引入大量运行时代码或循环依赖；将实用函数放在单独模块中。
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
