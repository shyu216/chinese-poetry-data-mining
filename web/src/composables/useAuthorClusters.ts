import { ref, computed, onMounted } from 'vue'
import type { AuthorCluster, AuthorNode, ClusterMetadata, ClusterFeatures } from '@/types/cluster'
import { getVerifiedCache } from './useVerifiedCache'

const metadata = ref<ClusterMetadata | null>(null)
const authors = ref<AuthorNode[]>([])
const features = ref<ClusterFeatures | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// 转换metadata中的clusters为数组
const clusters = computed<AuthorCluster[]>(() => {
  if (!metadata.value || !features.value) return []
  
  return Object.values(metadata.value.clusters).map(cluster => {
    const feature = features.value?.[cluster.id]
    return {
      ...cluster,
      center_3d: feature?.center_3d,
      top_words: feature?.top_words || [],
      poem_types: feature?.poem_types || [],
      avg_poems: feature?.avg_poems || 0
    }
  })
})

// 按聚类分组的诗人
const authorsByCluster = computed(() => {
  const grouped: Record<number, AuthorNode[]> = {}
  clusters.value.forEach(c => {
    grouped[c.id] = authors.value.filter(a => a.cluster === c.id)
  })
  return grouped
})

// 加载聚类数据
export function useAuthorClusters() {
  const loadClusters = async () => {
    if (metadata.value) return // 已加载

    loading.value = true
    error.value = null

    try {
      // 使用 hash 验证缓存加载聚类数据
      const [metaResult, authorsResult, featuresResult] = await Promise.all([
        getVerifiedCache<ClusterMetadata>(
          'author-clusters',
          'metadata',
          'author_clusters/clusters_metadata.json',
          async () => {
            const res = await fetch(`${import.meta.env.BASE_URL}/data/author_clusters/clusters_metadata.json`)
            if (!res.ok) throw new Error('Failed to load cluster metadata')
            return res.json()
          }
        ),
        getVerifiedCache<AuthorNode[]>(
          'author-clusters',
          'authors',
          'author_clusters/clusters_data.json',
          async () => {
            const res = await fetch(`${import.meta.env.BASE_URL}/data/author_clusters/clusters_data.json`)
            if (!res.ok) throw new Error('Failed to load cluster data')
            return res.json()
          }
        ),
        getVerifiedCache<ClusterFeatures>(
          'author-clusters',
          'features',
          'author_clusters/cluster_features.json',
          async () => {
            const res = await fetch(`${import.meta.env.BASE_URL}/data/author_clusters/cluster_features.json`)
            // 这个文件是可选的，失败时返回 null
            if (!res.ok) return null
            return res.json()
          }
        )
      ])

      if (metaResult.data) {
        metadata.value = metaResult.data
      }
      if (authorsResult.data) {
        authors.value = authorsResult.data
      }
      if (featuresResult.data) {
        features.value = featuresResult.data
      }

      console.log(`[AuthorClusters] Loaded ${authors.value.length} authors in ${clusters.value.length} clusters`)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('[AuthorClusters] Failed to load:', e)
    } finally {
      loading.value = false
    }
  }
  
  // 获取指定聚类的诗人
  const getAuthorsByCluster = (clusterId: number) => {
    return authors.value.filter(a => a.cluster === clusterId)
  }
  
  // 获取指定诗人
  const getAuthorByName = (name: string) => {
    return authors.value.find(a => a.name === name)
  }
  
  // 获取相似诗人
  const getSimilarAuthors = (authorName: string, limit: number = 5): AuthorNode[] => {
    const author = getAuthorByName(authorName)
    if (!author) return []
    
    return author.similar
      .map((name, idx) => ({
        author: getAuthorByName(name),
        score: author.similar_scores[idx]
      }))
      .filter(item => item.author)
      .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
      .slice(0, limit)
      .map(item => item.author!)
  }
  
  onMounted(() => {
    loadClusters()
  })
  
  return {
    // 状态
    loading,
    error,
    
    // 数据
    metadata,
    clusters,
    authors,
    features,
    authorsByCluster,
    
    // 方法
    loadClusters,
    getAuthorsByCluster,
    getAuthorByName,
    getSimilarAuthors
  }
}
