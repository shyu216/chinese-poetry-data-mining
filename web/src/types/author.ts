/**
 * @overview
 * file: web/src/types/author.ts
 * category: types
 * tech: TypeScript
 * solved: 提供领域模型与第三方库类型声明
 * data_source: TypeScript 声明系统
 * data_flow: 编译期参与类型推导与约束，不参与运行时数据流
 * complexity: 仅编译期类型约束，运行时开销 O(0)
 * unique: 核心导出: MeterPattern, SimilarAuthor, AuthorStats
 */
export interface MeterPattern {
  pattern: string
  count: number
}

export interface SimilarAuthor {
  author: string
  similarity: number
}

export interface AuthorStats {
  author: string
  poem_count: number
  poem_ids?: string[]
  poem_type_counts: Record<string, number>
  meter_patterns: MeterPattern[]
  word_frequency?: Record<string, number>
  similar_authors?: SimilarAuthor[]
}

export interface AuthorRank {
  rank: number
  author: string
  poem_count: number
  dynasty?: string
}
