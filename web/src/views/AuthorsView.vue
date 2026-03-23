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
import { getMetadata, getVerifiedChunkedCache } from '@/composables/useCacheV2'
import { AUTHORS_STORAGE } from '@/composables/useMetadataLoader'
import { useAuthorSearch } from '@/search'
import type { AuthorStats } from '@/types/author'
import { PageHeader, FilterSection } from '@/components/layout'
import { StatsCard } from '@/components/display'
import { ChunkLoaderStatus } from '@/components/feedback'
import { SearchContainer } from '@/components/search'
import { AuthorClusterViz } from '@/components/author'
import { useAuthorClusters } from '@/composables/useAuthorClusters'
import type { AuthorNode } from '@/types/cluster'
import { useLoading } from '@/composables/useLoading'

import { RankBadge, TypeDistribution } from '@/components/display'

const router = useRouter()
const loading = useLoading()
const {
  totalAuthors: totalAuthorsCount,
  totalChunks,
  loading: metadataLoading,
  loadMetadata,
  loadAuthorChunk
} = useAuthorsV2()

const { clusters, authors: clusterAuthors, loading: clusterLoading } = useAuthorClusters()

const chunkLoader = useChunkLoader()

const { search: searchAuthors, isReady: authorSearchReady } = useAuthorSearch()
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: '' })

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const loadedAuthors = ref<AuthorStats[]>([])
const hasMoreChunks = ref(true)
const isInitializing = ref(true)
const cachedChunksCount = ref(0)

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

const searchResults = ref<AuthorStats[]>([])
const searchTotal = ref(0)

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

const displayAuthors = computed(() => {
  const query = searchQuery.value.trim()
  if (query && authorSearchReady.value) {
    return searchResults.value
  }
  return filteredAuthors.value
})

const displayTotal = computed(() => {
  const query = searchQuery.value.trim()
  if (query && authorSearchReady.value) {
    return searchTotal.value
  }
  return filteredAuthors.value.length
})

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

const getTopPoemType = (typeCounts: Record<string, number>) => {
  const entries = Object.entries(typeCounts)
  if (entries.length === 0) return '-'
  const sorted = entries.sort((a, b) => b[1] - a[1])
  return sorted[0]?.[0] || '-'
}

const getTypeDistributionData = (typeCounts: Record<string, number>) => {
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

const loadCachedChunks = async (quickMode = false): Promise<number[]> => {
  console.log(`[AuthorsView] 🔄 开始加载本地缓存${quickMode ? ' (快速模式)' : ''}...`)
  const startTime = performance.now()

  const meta = await getMetadata(AUTHORS_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  console.log(`[AuthorsView] 📦 发现 ${loadedChunkIds.length} 个缓存分块`)

  if (loadedChunkIds.length === 0) {
    console.log('[AuthorsView] ⚠️ 无缓存数据，将从服务器加载')
    return []
  }

  // 快速模式：只读取第一个分块，立即展示
  if (quickMode) {
    const firstChunkId = loadedChunkIds[0]!
    console.log(`[AuthorsView] ⚡ 快速模式：优先加载分块 #${firstChunkId}`)

    const chunkData = await getVerifiedChunkedCache<AuthorStats[]>(AUTHORS_STORAGE, firstChunkId)

    if (chunkData && Array.isArray(chunkData) && chunkData.length > 0) {
      loadedAuthors.value = chunkData.sort((a, b) => b.poem_count - a.poem_count)
      cachedChunksCount.value = 1
      console.log(`[AuthorsView] ✅ 快速加载完成: ${chunkData.length} 位诗人 - ${Math.round(performance.now() - startTime)}ms`)
    }

    return [firstChunkId]
  }

  // 完整模式：读取所有缓存分块
  cachedChunksCount.value = loadedChunkIds.length
  const cachedAuthors: AuthorStats[] = []
  console.log(`[AuthorsView] 📖 开始读取 ${loadedChunkIds.length} 个缓存分块...`)
  for (const chunkId of loadedChunkIds) {
    const chunkStartTime = performance.now()
    const chunkData = await getVerifiedChunkedCache<AuthorStats[]>(AUTHORS_STORAGE, chunkId)
    const chunkDuration = Math.round(performance.now() - chunkStartTime)

    if (chunkData && Array.isArray(chunkData)) {
      cachedAuthors.push(...chunkData)
      console.log(`[AuthorsView]   ├─ 分块 #${chunkId}: ${chunkData.length} 位诗人 (${chunkDuration}ms)`)
    } else if (chunkData) {
      console.warn(`[AuthorsView]   ├─ 分块 #${chunkId}: 数据格式异常，已跳过`)
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

  loading.startBlocking('诗人名录', '正在开启诗人档案...')
  isInitializing.value = true

  try {
    loading.updatePhase('metadata', '正在读取诗人索引...')
    loading.updateProgress(0, 3)
    console.log('[AuthorsView] 📋 阶段1: 加载元数据...')
    const metaStartTime = performance.now()
    await loadMetadata()
    const totalChunksCount = totalChunks.value || 0
    console.log(`[AuthorsView] ✅ 元数据加载完成: ${totalAuthorsCount.value} 位诗人, ${totalChunksCount} 个分块 - ${Math.round(performance.now() - metaStartTime)}ms`)

    // 步骤2: 快速加载第一个缓存分块（渐进式加载核心）
    loading.updateProgress(1, 3, '正在加载首批诗人...')
    console.log('[AuthorsView] ⚡ 阶段2: 快速加载首批数据...')
    const quickStartTime = performance.now()
    const firstChunkIds = await loadCachedChunks(true) // true = 快速模式
    console.log(`[AuthorsView] ✅ 首批数据加载完成 - ${Math.round(performance.now() - quickStartTime)}ms`)

    // 步骤3: 立即解除阻塞，展示界面！
    loading.updateProgress(2, 3, '准备就绪...')
    loading.updatePhase('complete', '诗人档案已备，请君查阅')
    loading.updateProgress(3, 3)
    setTimeout(() => loading.finish(), 200)
    isInitializing.value = false

    console.log('[AuthorsView] � 界面已可交互，开始后台加载剩余数据...')

    // 步骤4: 后台加载剩余缓存 + 网络数据
    const remainingStartTime = performance.now()
    loading.startNonBlocking('补充诗人数据', '正在汇聚千年文脉...')

    // 先加载剩余缓存分块
    const meta = await getMetadata(AUTHORS_STORAGE)
    const allCachedChunkIds = meta?.loadedChunkIds || []
    const remainingCachedIds = allCachedChunkIds.filter(id => !firstChunkIds.includes(id))

    if (remainingCachedIds.length > 0) {
      console.log(`[AuthorsView] � 后台加载剩余 ${remainingCachedIds.length} 个缓存分块...`)
      for (const chunkId of remainingCachedIds) {
        const chunkData = await getVerifiedChunkedCache<AuthorStats[]>(AUTHORS_STORAGE, chunkId)
        if (chunkData && Array.isArray(chunkData)) {
          loadedAuthors.value.push(...chunkData)
          cachedChunksCount.value++
        }
      }
      // 重新排序
      loadedAuthors.value.sort((a, b) => b.poem_count - a.poem_count)
      console.log(`[AuthorsView] ✅ 剩余缓存加载完成，当前共 ${loadedAuthors.value.length} 位诗人`)
    }

    // 加载网络分块
    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !allCachedChunkIds.includes(id))

    if (unloadedChunkIds.length === 0) {
      console.log('[AuthorsView] ✨ 所有数据已加载完成')
      hasMoreChunks.value = false
      loading.finish()
    } else {
      console.log(`[AuthorsView] 🌐 开始加载 ${unloadedChunkIds.length} 个网络分块...`)
      let loadedCount = allCachedChunkIds.length
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
          const progress = Math.round((loadedCount / totalChunksCount) * 100)

          if (loadedCount % Math.max(1, Math.floor(totalChunksCount / 10)) === 0) {
            const phases = ['正在读取诗人档案...', '正在整理诗作数据...', '正在汇聚千年文脉...', '正在构建诗人图谱...']
            const phase = phases[Math.floor((loadedCount / totalChunksCount) * phases.length)] || phases[0]
            loading.updateProgress(loadedCount, totalChunksCount, `${phase} (${loadedCount}/${totalChunksCount})`)
            console.log(`[AuthorsView] 📥 后台加载进度: ${progress}% (${loadedCount}/${totalChunksCount} 分块, +${networkDataCount} 位诗人)`)
          }
        },
        onComplete: () => {
          const bgDuration = Math.round(performance.now() - remainingStartTime)
          console.log(`[AuthorsView] ✅ 后台加载完成: 共 ${loadedAuthors.value.length} 位诗人 - ${bgDuration}ms`)
          hasMoreChunks.value = false
          loading.finish()
        }
      })
    }
  } catch (error) {
    loading.error('加载失败，请刷新重试')
    console.error('[AuthorsView] ❌ 诗人数据加载失败:', error)
    isInitializing.value = false
  } finally {
    const totalDuration = Math.round(performance.now() - totalStartTime)
    console.log(`[AuthorsView] 🏁 总加载时间: ${totalDuration}ms`)
  }
}

const goToAuthorDetail = (author: AuthorStats) => {
  router.push(`/authors/${encodeURIComponent(author.author)}`)
}

const onSelectClusterAuthor = (author: AuthorNode) => {
  router.push(`/authors/${encodeURIComponent(author.name)}`)
}

const onSelectCluster = (clusterId: number) => {
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
          <RankBadge :rank="author.rank" size="large" />

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

          <div class="type-distribution-wrapper">
            <TypeDistribution
              :data="getTypeDistributionData(author.poem_type_counts)"
              :show-percentage="false"
              size="small"
            />
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

.type-distribution-wrapper {
  width: 200px;
  flex-shrink: 0;
}

.arrow-icon {
  width: 20px;
  height: 20px;
  opacity: 0.3;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.author-item-move,
.author-item-enter-active,
.author-item-leave-active {
  transition: all 0.3s ease;
}

.author-item-enter-from,
.author-item-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.author-item-leave-active {
  position: absolute;
}

@media (max-width: 768px) {
  .authors-view {
    padding: 16px;
  }

  .author-card {
    flex-wrap: wrap;
    gap: 12px;
    padding: 16px;
  }

  .type-distribution-wrapper {
    width: 100%;
    order: 3;
  }

  .arrow-icon {
    order: 4;
  }
}
</style>
