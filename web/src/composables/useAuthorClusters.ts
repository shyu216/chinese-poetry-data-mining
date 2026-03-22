import { ref, computed, onMounted } from 'vue'
import type { AuthorCluster, AuthorNode, ClusterMetadata, ClusterFeatures } from '@/types/cluster'

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
      // 加载元数据
      const metaRes = await fetch(`${import.meta.env.BASE_URL}/data/author_clusters/clusters_metadata.json`)
      if (!metaRes.ok) throw new Error('Failed to load cluster metadata')
      metadata.value = await metaRes.json()
      
      // 加载诗人数据
      const authorsRes = await fetch(`${import.meta.env.BASE_URL}/data/author_clusters/clusters_data.json`)
      if (!authorsRes.ok) throw new Error('Failed to load cluster data')
      authors.value = await authorsRes.json()
      
      // 加载详细特征
      const featuresRes = await fetch(`${import.meta.env.BASE_URL}/data/author_clusters/cluster_features.json`)
      if (featuresRes.ok) {
        features.value = await featuresRes.json()
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
