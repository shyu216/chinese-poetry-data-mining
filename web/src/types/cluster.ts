// 诗人聚类相关类型定义

export interface ClusterWord {
  word: string
  ratio: number
  count: number
}

export interface ClusterPoemType {
  type: string
  count: number
}

export interface AuthorCluster {
  id: number
  name: string
  size: number
  color: string
  center_2d: [number, number]
  center_3d?: [number, number, number]
  representatives: string[]
  top_words: ClusterWord[]
  poem_types: ClusterPoemType[]
  avg_poems: number
}

export interface AuthorNode {
  id: number
  name: string
  cluster: number
  poem_count: number
  main_type: string
  coord_2d: [number, number]
  coord_3d?: [number, number, number]
  similar: string[]
  similar_scores: number[]
}

export interface ClusterMetadata {
  version: string
  total_authors: number
  n_clusters: number
  min_poems: number
  clusters: Record<string, {
    id: number
    name: string
    size: number
    color: string
    center_2d: [number, number]
    representatives: string[]
  }>
}

export interface ClusterFeatures {
  [clusterId: string]: AuthorCluster
}
