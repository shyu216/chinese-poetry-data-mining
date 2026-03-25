/**
 * @overview
 * file: web/src/composables/useAuthorClusters.ts
 * category: pipeline / composable
 * tech: Vue 3 + TypeScript
 * summary: 管理并加载诗人流派（聚类）数据，提供给可视化组件与视图使用。
 *
 * Data pipeline:
 *  - 输入: 无需外部参数（默认从 `public/data/author_clusters` 加载固定 JSON 文件）
 *  - 读取: 并行 fetch 两个 JSON 文件（analysis_spectral.json, clusters_data.json）
 *  - 验证/解析: 解析 JSON -> 归一化为内部类型 (`clustersData`, `authorsData`)
 *  - 输出: 暴露响应式状态与帮助函数（`loadClusters`, `getClusterColor`, `getClusterName`, `calculateClusterCenter`）供组件消费
 *
 * Complexity:
 *  - 网络/解析: 单次文件解析为 O(n)（n = 文件内记录数）；两文件并行加载总体仍为 O(n)
 *  - 查询/过滤: 计算簇中心或筛选作者为 O(a)（a = 作者数量）
 *  - 排序（若使用）为 O(a log a)
 *  - 空间: 内存占用近似 O(a + k)（a = 作者数, k = 聚类数）
 *
 * Exports / responsibilities:
 *  - `useAuthorClusters()` -> 提供 `loadClusters()`, `clustersData`, `authorsData`, `loading`, `error`, `calculateClusterCenter`, `getClusterColor`, `getClusterName`
 *
 * Potential issues & recommendations:
 *  - 大文件风险: 作者列表较大时 JSON 解析可能阻塞主线程。建议将解析或大型聚合移动到 Web Worker 或使用分块/流式解析。
 *  - 可用性: getClusterName 依赖文件内字段，缺失字段需有良好回退（已提供基础回退）。
 *  - 网络鲁棒性: 建议添加重试、超时与后备降级（例如仅加载小型摘要）。
 *  - 渲染性能: 在列表或可视化中渲染大量作者时使用虚拟列表或分层渲染以避免 DOM 爆炸。
 */

import { ref, computed } from 'vue'
import type { AuthorCluster, AuthorNode, ClusterWord } from '@/types/cluster'

// 原始数据接口
interface RawCluster {
  size: number
  representative_authors: string[]
  avg_poems: number
  top_words: string[]
  distinctive_words: Array<{
    word: string
    ratio: number
    count: number
  }>
  poem_types: Array<{
    type: string
    count: number
  }>
  patterns: Array<{
    pattern: string
    count: number
  }>
}

interface RawClusterData {
  algorithm: string
  n_clusters: number
  total_authors: number
  feature_weights: {
    words: number
    types: number
    patterns: number
  }
  clusters: Record<string, RawCluster>
}

interface RawAuthorNode {
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

// 流派颜色映射
const clusterColors = [
  '#8B2635', // 深红
  '#1E40AF', // 深蓝
  '#047857', // 深绿
  '#B45309', // 深橙
  '#7C3AED', // 紫色
  '#DC2626', // 红色
  '#0891B2', // 青色
  '#6B7280'  // 灰色
]

export function useAuthorClusters() {
  const clustersData = ref<RawClusterData | null>(null)
  const authorsData = ref<RawAuthorNode[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 加载聚类数据
  const loadClusters = async () => {
    loading.value = true
    error.value = null

    try {
      const baseUrl = import.meta.env.BASE_URL || '/'

      // 并行加载两个数据文件
      const [analysisResponse, authorsResponse] = await Promise.all([
        fetch(`${baseUrl}data/author_clusters/analysis_spectral.json`.replace(/\/+/g, '/')),
        fetch(`${baseUrl}data/author_clusters/clusters_data.json`.replace(/\/+/g, '/'))
      ])

      if (!analysisResponse.ok) {
        throw new Error('Failed to load cluster analysis')
      }
      if (!authorsResponse.ok) {
        throw new Error('Failed to load cluster authors data')
      }

      clustersData.value = await analysisResponse.json()
      authorsData.value = await authorsResponse.json()

      console.log('[useAuthorClusters] Loaded:', {
        clusters: Object.keys(clustersData.value?.clusters || {}).length,
        authors: authorsData.value.length
      })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('Failed to load clusters:', e)
    } finally {
      loading.value = false
    }
  }

  // 计算聚类中心坐标
  const calculateClusterCenter = (clusterId: number): [number, number] => {
    const clusterAuthors = authorsData.value.filter(a => a.cluster === clusterId)
    if (clusterAuthors.length === 0) return [0, 0]

    const sumX = clusterAuthors.reduce((sum, a) => sum + a.coord_2d[0], 0)
    const sumY = clusterAuthors.reduce((sum, a) => sum + a.coord_2d[1], 0)

    return [
      sumX / clusterAuthors.length,
      sumY / clusterAuthors.length
    ]
  }

  // 获取聚类颜色（支持字符串和数字ID）
  const getClusterColor = (id: string | number): string => {
    const index = typeof id === 'string' ? parseInt(id) : id
    const color = clusterColors[index % clusterColors.length]
    return color ?? '#8B2635'
  }

  // 获取聚类名称（旧版API，支持字符串ID）
  const getClusterName = (id: string | number): string => {
    const strId = typeof id === 'number' ? String(id) : id
    const cluster = clustersData.value?.clusters[strId]
    if (!cluster) return `流派 ${id}`

    // 使用 distinctive_words 前两个关键词组合命名
    if (cluster.distinctive_words && cluster.distinctive_words.length >= 2) {
      const word1 = cluster.distinctive_words[0]?.word
      const word2 = cluster.distinctive_words[1]?.word
      if (word1 && word2) {
        return `${word1}·${word2}派`
      }
    }
    // 回退：使用 top_words
    if (cluster.top_words && cluster.top_words.length >= 2) {
      return `${cluster.top_words[0]}·${cluster.top_words[1]}派`
    }
    return `流派 ${id}`
  }

  // 转换 top_words 格式
  const convertTopWords = (cluster: RawCluster): ClusterWord[] => {
    // 使用 distinctive_words 作为词频数据（包含 ratio 和 count）
    if (cluster.distinctive_words && cluster.distinctive_words.length > 0) {
      return cluster.distinctive_words.slice(0, 10).map(dw => ({
        word: dw.word,
        ratio: dw.ratio,
        count: dw.count
      }))
    }
    // 回退：从 top_words 创建虚拟数据
    return cluster.top_words.slice(0, 10).map(word => ({
      word,
      ratio: 1.0,
      count: 0
    }))
  }

  // 新版：转换后的聚类数据（用于可视化组件，id为数字）
  const sortedClusters = computed<AuthorCluster[]>(() => {
    if (!clustersData.value) return []

    return Object.entries(clustersData.value.clusters)
      .map(([idStr, cluster]) => {
        const id = parseInt(idStr)
        return {
          id,
          name: getClusterName(id),
          size: cluster.size,
          color: getClusterColor(id),
          center_2d: calculateClusterCenter(id),
          center_3d: undefined,
          representatives: cluster.representative_authors,
          top_words: convertTopWords(cluster),
          poem_types: cluster.poem_types,
          avg_poems: Math.round(cluster.avg_poems)
        }
      })
      .sort((a, b) => b.size - a.size)
  })

  // 旧版：保持原始格式的聚类数据（用于兼容旧组件，id为字符串）
  const clusters = computed(() => {
    if (!clustersData.value) return []

    return Object.entries(clustersData.value.clusters)
      .map(([id, cluster]) => ({
        id, // 字符串ID
        ...cluster,
        color: getClusterColor(id),
        name: getClusterName(id)
      }))
      .sort((a, b) => b.size - a.size)
  })

  // 转换后的诗人节点数据
  const authorNodes = computed<AuthorNode[]>(() => {
    return authorsData.value.map(author => ({
      id: author.id,
      name: author.name,
      cluster: author.cluster,
      poem_count: author.poem_count,
      main_type: author.main_type,
      coord_2d: author.coord_2d,
      coord_3d: author.coord_3d,
      similar: author.similar,
      similar_scores: author.similar_scores
    }))
  })

  // 按聚类分组的诗人
  const authorsByCluster = computed(() => {
    const grouped: Record<number, AuthorNode[]> = {}
    sortedClusters.value.forEach(c => {
      grouped[c.id] = authorNodes.value.filter(a => a.cluster === c.id)
    })
    return grouped
  })

  // 获取单个聚类（新版API，返回AuthorCluster格式）
  const getCluster = (id: string | number) => {
    return computed(() => {
      const numId = typeof id === 'string' ? parseInt(id) : id
      return sortedClusters.value.find(c => c.id === numId) || null
    })
  }

  const totalClusters = computed(() => {
    return clustersData.value?.n_clusters || 0
  })

  const totalAuthors = computed(() => {
    return clustersData.value?.total_authors || 0
  })

  return {
    clustersData,
    authorsData,
    loading,
    error,
    loadClusters,
    sortedClusters,
    clusters, // 旧版格式
    authorNodes,
    authorsByCluster,
    getCluster,
    getClusterColor,
    getClusterName,
    totalClusters,
    totalAuthors
  }
}
