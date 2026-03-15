export interface MeterPattern {
  pattern: string
  count: number
}

export interface AuthorStats {
  author: string
  poem_count: number
  poem_type_counts: Record<string, number>
  meter_patterns: MeterPattern[]
}

export interface AuthorRank {
  rank: number
  author: string
  poem_count: number
  dynasty?: string
}
