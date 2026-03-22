<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NEmpty, NInput, NSpace, NTag,
  NButton, NPagination, NGrid, NGridItem
} from 'naive-ui'
import {
  TrophyOutline, PersonOutline, BookOutline,
  SearchOutline, MedalOutline, BarChartOutline,
  ChevronForwardOutline
} from '@vicons/ionicons5'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { getMetadata, getChunkedCache } from '@/composables/useCacheV2'
import { AUTHORS_STORAGE } from '@/composables/useMetadataLoader'
import { useAuthorSearch } from '@/search'
import type { AuthorStats } from '@/types/author'
import PageHeader from '@/components/PageHeader.vue'
import FilterSection from '@/components/FilterSection.vue'
import StatsCard from '@/components/StatsCard.vue'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'
import { SearchContainer } from '@/components/search'
import AuthorClusterViz from '@/components/AuthorClusterViz.vue'
import { useAuthorClusters } from '@/composables/useAuthorClusters'
import type { AuthorNode } from '@/types/cluster'
import { useLoading } from '@/composables/useLoading'

const router = useRouter()
const globalLoading = useLoading()
const {
  totalAuthors: totalAuthorsCount,
  totalChunks,
  loading: metadataLoading,
  loadMetadata,
  loadAuthorChunk
} = useAuthorsV2()

// 聚类数据
const { clusters, authors: clusterAuthors, loading: clusterLoading } = useAuthorClusters()

const chunkLoader = useChunkLoader()

// 新的作者搜索模块
const { search: searchAuthors, isReady: authorSearchReady } = useAuthorSearch()
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: '' })

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const loadedAuthors = ref<AuthorStats[]>([])
const hasMoreChunks = ref(true)
const isInitializing = ref(true)
const cachedChunksCount = ref(0) // 从 IndexedDB 缓存的 chunk 数量

const dynamicStats = computed(() => {
  const list = loadedAuthors.value
  const total = list.length
  const topAuthor = list[0]?.author || '-'
  const maxPoems = list[0]?.poem_count || 0
  const totalPoems = list.reduce((sum, a) => sum + (a.poem_count || 0), 0)
  const average = total > 0 ? Math.round(totalPoems / total) : 0

  return {
    total,
    topAuthor,
    maxPoems,
    totalPoems,
    average
  }
})

const filteredAuthors = computed(() => {
  // 如果有搜索且 AuthorSearch 已就绪，返回空（使用搜索结果）
  if (searchQuery.value.trim() && authorSearchReady.value && isSearching.value) {
    return []
  }
  if (!searchQuery.value.trim()) {
    return loadedAuthors.value
  }
  const query = searchQuery.value.toLowerCase()
  return loadedAuthors.value.filter(a =>
    a.author.toLowerCase().includes(query)
  )
})

// 搜索结果
const searchResults = ref<AuthorStats[]>([])
const searchTotal = ref(0)

// 使用 AuthorSearch 搜索
const performSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query || !authorSearchReady.value) {
    searchResults.value = []
    searchTotal.value = 0
    return
  }

  isSearching.value = true
  try {
    const result = await searchAuthors(query, {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
    searchResults.value = result.items
    searchTotal.value = result.total
    searchStats.value = { queryTime: result.queryTime, source: result.source }
  } finally {
    isSearching.value = false
  }
}

// 最终显示的作者列表
const displayAuthors = computed(() => {
  const query = searchQuery.value.trim()
  if (query && authorSearchReady.value) {
    return searchResults.value
  }
  return filteredAuthors.value
})

// 显示的总数（用于搜索统计）
const displayTotal = computed(() => {
  const query = searchQuery.value.trim()
  if (query && authorSearchReady.value) {
    return searchTotal.value
  }
  return filteredAuthors.value.length
})

// 总页数
const totalPages = computed(() => {
  const query = searchQuery.value.trim()
  if (query && authorSearchReady.value) {
    return Math.ceil(searchTotal.value / pageSize.value)
  }
  return Math.ceil(filteredAuthors.value.length / pageSize.value)
})

const paginatedAuthors = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return displayAuthors.value.slice(start, end).map((author, index) => ({
    ...author,
    rank: start + index + 1
  }))
})

const getRankColor = (rank: number) => {
  if (rank === 1) return '#FFD700'
  if (rank === 2) return '#C0C0C0'
  if (rank === 3) return '#CD7F32'
  return '#8b7355'
}

const getRankIcon = (rank: number) => {
  if (rank <= 3) return '🏆'
  if (rank <= 10) return '🥇'
  if (rank <= 50) return '🥈'
  return '🥉'
}

const getTopPoemType = (typeCounts: Record<string, number>) => {
  const entries = Object.entries(typeCounts)
  if (entries.length === 0) return '-'
  const sorted = entries.sort((a, b) => b[1] - a[1])
  return sorted[0]?.[0] || '-'
}

const getTypeDistribution = (typeCounts: Record<string, number>) => {
  const total = Object.values(typeCounts).reduce((a, b) => a + b, 0)
  const entries = Object.entries(typeCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)

  return entries.map(([type, count]) => ({
    type,
    count,
    percentage: Math.round((count / total) * 100)
  }))
}

const loadingHint = computed(() => {
  const count = loadedAuthors.value.length
  if (count === 0) return '🚀 正在连接...'
  if (count === 1) return `🏆 冠军登场：${loadedAuthors.value[0]?.author}！`
  if (count === 2) return `🥈 亚军揭晓：${loadedAuthors.value[1]?.author}！`
  if (count === 3) return `🥉 季军出炉：${loadedAuthors.value[2]?.author}！`
  return `📚 已加载 ${count.toLocaleString()} 位诗人...`
})

// 从 IndexedDB 加载缓存的 chunk 数据
const loadCachedChunks = async (): Promise<number[]> => {
  console.log('[AuthorsView] 🔄 开始加载本地缓存...')
  const startTime = performance.now()

  const meta = await getMetadata(AUTHORS_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  // 更新缓存的 chunk 数量
  cachedChunksCount.value = loadedChunkIds.length
  console.log(`[AuthorsView] 📦 发现 ${loadedChunkIds.length} 个缓存分块`)

  if (loadedChunkIds.length === 0) {
    console.log('[AuthorsView] ⚠️ 无缓存数据，将从服务器加载')
    return []
  }

  // 从 IndexedDB 读取每个 chunk 的数据
  const cachedAuthors: AuthorStats[] = []
  console.log(`[AuthorsView] 📖 开始读取 ${loadedChunkIds.length} 个缓存分块...`)
  for (const chunkId of loadedChunkIds) {
    const chunkStartTime = performance.now()
    const chunkData = await getChunkedCache<AuthorStats[]>(AUTHORS_STORAGE, chunkId)
    const chunkDuration = Math.round(performance.now() - chunkStartTime)

    if (chunkData) {
      cachedAuthors.push(...chunkData)
      console.log(`[AuthorsView]   ├─ 分块 #${chunkId}: ${chunkData.length} 位诗人 (${chunkDuration}ms)`)
    }
  }

  if (cachedAuthors.length > 0) {
    loadedAuthors.value = cachedAuthors.sort((a, b) => b.poem_count - a.poem_count)
  }

  const totalDuration = Math.round(performance.now() - startTime)
  console.log(`[AuthorsView] ✅ 缓存加载完成: ${cachedAuthors.length} 位诗人 - ${totalDuration}ms`)

  return loadedChunkIds
}

const loadData = async () => {
  console.log('[AuthorsView] 🚀 开始加载数据...')
  const totalStartTime = performance.now()

  // 阶段1：阻塞性加载 - 元数据和搜索索引（必须等待）
  const initTaskId = globalLoading.startBlocking(
    '准备诗人群像',
    '正在建立数据连接...'
  )

  isInitializing.value = true
  try {
    // 阶段1：加载元数据
    globalLoading.update(initTaskId, { phase: 'meta' })
    console.log('[AuthorsView] 📋 阶段1: 加载元数据...')
    const metaStartTime = performance.now()
    await loadMetadata()
    const totalChunksCount = totalChunks.value || 0
    console.log(`[AuthorsView] ✅ 元数据加载完成: ${totalAuthorsCount.value} 位诗人, ${totalChunksCount} 个分块 - ${Math.round(performance.now() - metaStartTime)}ms`)

    // 阶段2：检查缓存（快速操作）
    globalLoading.update(initTaskId, {
      phase: 'search',
      description: '正在检查本地缓存...',
      progress: 30
    })
    console.log('[AuthorsView] 💾 阶段2: 检查本地缓存...')
    const cacheStartTime = performance.now()
    const loadedChunkIds = await loadCachedChunks()
    console.log(`[AuthorsView] ✅ 缓存检查完成 - ${Math.round(performance.now() - cacheStartTime)}ms`)

    // 阶段3：UI 准备
    globalLoading.update(initTaskId, {
      phase: 'ui',
      description: '正在调整布局...',
      progress: 50
    })
    console.log('[AuthorsView] 🎨 阶段3: 准备UI...')
    const uiStartTime = performance.now()

    // 只加载未加载的 chunk
    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))
    console.log(`[AuthorsView] 📊 需要加载的分块: ${unloadedChunkIds.length} 个 (已缓存: ${loadedChunkIds.length} 个)`)
    console.log(`[AuthorsView] ✅ UI准备完成 - ${Math.round(performance.now() - uiStartTime)}ms`)

    // 完成阻塞性加载，用户可以开始交互了
    globalLoading.update(initTaskId, {
      description: '准备就绪',
      progress: 100
    })
    setTimeout(() => globalLoading.finish(initTaskId), 200)

    // 如果没有需要加载的 chunk，直接返回
    if (unloadedChunkIds.length === 0) {
      console.log('[AuthorsView] ✨ 所有数据已从缓存加载，无需网络请求')
      hasMoreChunks.value = false
      isInitializing.value = false
      return
    }

    // 阶段4：后台加载剩余数据（不阻塞用户交互）
    console.log('[AuthorsView] 🌐 阶段4: 开始后台加载网络数据...')
    const bgStartTime = performance.now()
    const bgTaskId = globalLoading.startBackground(
      '补充诗人数据',
      '正在汇聚千年文脉...'
    )

    let loadedCount = loadedChunkIds.length
    const totalCount = totalChunksCount
    let networkDataCount = 0

    await chunkLoader.loadChunks<AuthorStats[]>(unloadedChunkIds, loadAuthorChunk, {
      concurrency: 5,
      chunkDelay: 0,
      onChunkLoaded: (chunkId, authors) => {
        const authorsArray = authors as AuthorStats[]
        loadedAuthors.value.push(...authorsArray)
        loadedAuthors.value.sort((a, b) => b.poem_count - a.poem_count)
        networkDataCount += authorsArray.length

        loadedCount++
        const progress = Math.round((loadedCount / totalCount) * 100)

        // 每加载10%更新一次提示
        if (loadedCount % Math.max(1, Math.floor(totalCount / 10)) === 0) {
          const phases = ['正在读取诗人档案...', '正在整理诗作数据...', '正在汇聚千年文脉...', '正在构建诗人图谱...']
          const phase = phases[Math.floor((loadedCount / totalCount) * phases.length)] || phases[0]
          globalLoading.update(bgTaskId, {
            description: `${phase} (${loadedCount}/${totalCount})`,
            progress,
            current: loadedCount,
            total: totalCount
          })
          console.log(`[AuthorsView] 📥 后台加载进度: ${progress}% (${loadedCount}/${totalCount} 分块, ${networkDataCount} 位诗人)`)
        }
      },
      onComplete: () => {
        const bgDuration = Math.round(performance.now() - bgStartTime)
        console.log(`[AuthorsView] ✅ 后台加载完成: ${networkDataCount} 位诗人 - ${bgDuration}ms`)
        hasMoreChunks.value = false
        globalLoading.finish(bgTaskId)
      }
    })
  } catch (error) {
    globalLoading.update(initTaskId, { description: '加载失败，请刷新重试' })
    console.error('[AuthorsView] ❌ 诗人数据加载失败:', error)
  } finally {
    const totalDuration = Math.round(performance.now() - totalStartTime)
    console.log(`[AuthorsView] 🏁 总加载时间: ${totalDuration}ms`)
    isInitializing.value = false
  }
}

const goToAuthorDetail = (author: AuthorStats) => {
  router.push(`/authors/${encodeURIComponent(author.author)}`)
}

// 从聚组件点击诗人跳转
const onSelectClusterAuthor = (author: AuthorNode) => {
  router.push(`/authors/${encodeURIComponent(author.name)}`)
}

// 从聚类组件点击流派筛选
const onSelectCluster = (clusterId: number) => {
  // 可以扩展为筛选显示该流派的诗人
  console.log('Selected cluster:', clusterId)
}

onMounted(() => {
  loadData()
})

watch(searchQuery, () => {
  currentPage.value = 1
  performSearch()
})
</script>

<template>
  <div class="authors-view">
    <PageHeader
      title="诗人排行榜"
      :subtitle="`收录 ${dynamicStats.total} 位诗人，按诗词数量排序`"
      :icon="TrophyOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard
          label="总收录诗人"
          :value="dynamicStats.total"
          :prefix-icon="PersonOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="诗词最多"
          :value="dynamicStats.topAuthor"
          :prefix-icon="MedalOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="最高产量"
          :value="dynamicStats.maxPoems"
          suffix="首"
          :prefix-icon="BookOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="平均产量"
          :value="dynamicStats.average"
          suffix="首"
          :prefix-icon="BarChartOutline"
        />
      </NGridItem>
    </NGrid>
    
    <!-- 诗人聚类可视化 -->
    <AuthorClusterViz
      :clusters="clusters"
      :authors="clusterAuthors"
      :loading="clusterLoading"
      @select-author="onSelectClusterAuthor"
      @select-cluster="onSelectCluster"
    />

    <ChunkLoaderStatus
      v-if="chunkLoader.isLoading.value || cachedChunksCount > 0"
      :is-loading="chunkLoader.isLoading.value"
      :is-paused="chunkLoader.isPaused.value"
      :progress="Math.round(((cachedChunksCount + chunkLoader.loadedCount.value) / (totalChunks || 1)) * 100)"
      :loaded-count="cachedChunksCount + chunkLoader.loadedCount.value"
      :total-count="totalChunks || 0"
      title="加载诗人数据"
      :hint="loadingHint"
      :stats="[
        { label: '已收录诗词', value: dynamicStats.totalPoems.toLocaleString() + ' 首' },
        { label: '当前平均', value: dynamicStats.average + ' 首/人' }
      ]"
      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
    />

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索诗人..."
      size="large"
      :width="300"
      :total="displayTotal"
      :query-time="searchStats.queryTime"
      :source="searchStats.source as any"
      :loading="isSearching"
    />

    <NEmpty v-if="!isInitializing && loadedAuthors.length === 0" description="暂无诗人数据" />

    <div v-else class="authors-list">
        <TransitionGroup name="author-item">
          <div
            v-for="author in paginatedAuthors"
            :key="author.author"
            class="author-card"
            :class="{ 'top-three': author.rank <= 3 }"
            @click="goToAuthorDetail(author)"
          >
            <div class="rank-badge" :style="{ backgroundColor: getRankColor(author.rank) }">
              <span class="rank-number">{{ author.rank }}</span>
              <span class="rank-icon">{{ getRankIcon(author.rank) }}</span>
            </div>

            <div class="author-info">
              <h3 class="author-name">{{ author.author }}</h3>
              <div class="author-stats">
                <NTag type="primary" size="small">
                  {{ author.poem_count }} 首诗词
                </NTag>
                <span class="top-type">
                  擅长：{{ getTopPoemType(author.poem_type_counts) }}
                </span>
              </div>
            </div>

            <div class="type-distribution">
              <div
                v-for="item in getTypeDistribution(author.poem_type_counts)"
                :key="item.type"
                class="type-bar"
              >
                <span class="type-label">{{ item.type }}</span>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: item.percentage + '%' }"></div>
                </div>
                <span class="type-count">{{ item.count }}</span>
              </div>
            </div>

            <ChevronForwardOutline class="arrow-icon" />
          </div>
        </TransitionGroup>
      </div>

    <div class="pagination-wrapper" v-if="totalPages > 1">
      <NPagination
        v-model:page="currentPage"
        :page-count="totalPages"
        :page-size="pageSize"
        show-size-picker
        :page-sizes="[10, 20, 50, 100]"
        @update:page-size="pageSize = $event"
      />
    </div>
  </div>
</template>

<style scoped>
.authors-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.stats-grid {
  margin-bottom: 24px;
}

.search-section {
  margin-bottom: 24px;
}

.authors-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.author-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.author-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  border-color: var(--color-seal, #8b2635);
}

.author-card:hover .arrow-icon {
  opacity: 1;
  color: var(--color-seal, #8b2635);
  transform: translateX(4px);
}

.author-card.top-three {
  background: linear-gradient(135deg, #fff 0%, #fdf6f0 100%);
  border: 1px solid #e8d5c4;
}

.rank-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  color: #fff;
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.rank-number {
  font-size: 20px;
  line-height: 1;
}

.rank-icon {
  font-size: 14px;
  margin-top: 2px;
}

.author-info {
  flex: 1;
  min-width: 0;
}

.author-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  margin: 0 0 8px 0;
}

.author-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-type {
  font-size: 14px;
  color: var(--color-ink-light, #666);
}

.type-distribution {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 200px;
  flex-shrink: 0;
}

.type-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-label {
  font-size: 12px;
  color: var(--color-ink-light, #666);
  width: 60px;
  flex-shrink: 0;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-seal, #8b2635);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.type-count {
  font-size: 12px;
  color: #999;
  width: 30px;
  text-align: right;
}

.arrow-icon {
  width: 20px;
  height: 20px;
  color: var(--color-ink-light, #999);
  opacity: 0;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.pagination-wrapper {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

.author-item-enter-active,
.author-item-leave-active {
  transition: all 0.5s ease;
}

.author-item-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.author-item-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

@media (max-width: 768px) {
  .authors-view {
    padding: 16px;
  }

  .author-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .type-distribution {
    width: 100%;
  }

  .arrow-icon {
    display: none;
  }
}
</style>
