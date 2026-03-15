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
