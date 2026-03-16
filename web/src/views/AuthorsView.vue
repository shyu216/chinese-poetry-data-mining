<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NSpin, NEmpty, NInput, NSpace, NTag,
  NButton, NPagination, NGrid, NGridItem,
  NProgress, NDivider
} from 'naive-ui'
import {
  TrophyOutline, PersonOutline, BookOutline,
  SearchOutline, MedalOutline, BarChartOutline,
  ChevronForwardOutline, PauseOutline, PlayOutline,
  DownloadOutline
} from '@vicons/ionicons5'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import type { AuthorStats } from '@/types/author'
import PageHeader from '@/components/PageHeader.vue'
import FilterSection from '@/components/FilterSection.vue'
import StatsCard from '@/components/StatsCard.vue'

const router = useRouter()
const {
  totalAuthors: totalAuthorsCount,
  totalChunks,
  loadedChunkCount,
  loading,
  loadMetadata,
  getAuthorsByChunk,
  getLoadedAuthors,
  preloadChunks,
  metadata
} = useAuthorsV2()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const loadedAuthors = ref<AuthorStats[]>([])
const loadProgress = ref(0)
const isLoadingInitial = ref(true)
const isPaused = ref(false)
const isLoadingChunk = ref(false)
const listContainerRef = ref<HTMLElement | null>(null)

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
  if (!searchQuery.value.trim()) {
    return loadedAuthors.value
  }
  const query = searchQuery.value.toLowerCase()
  return loadedAuthors.value.filter(a =>
    a.author.toLowerCase().includes(query)
  )
})

const displayAuthors = computed(() => {
  return filteredAuthors.value
})

const paginatedAuthors = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return displayAuthors.value.slice(start, end).map((author, index) => ({
    ...author,
    rank: start + index + 1
  }))
})

const totalPages = computed(() => Math.ceil(displayAuthors.value.length / pageSize.value))

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

const hasMoreChunks = computed(() => {
  return loadedChunkCount.value < (totalChunks.value || 0)
})

const loadingHint = computed(() => {
  const count = loadedAuthors.value.length
  if (count === 0) return '🚀 正在连接...'
  if (count === 1) return `🏆 冠军登场：${loadedAuthors.value[0]?.author}！`
  if (count === 2) return `🥈 亚军揭晓：${loadedAuthors.value[1]?.author}！`
  if (count === 3) return `🥉 季军出炉：${loadedAuthors.value[2]?.author}！`
  if (isPaused.value) return `⏸️ 已暂停 · 已加载 ${count.toLocaleString()} 位诗人`
  return `📚 已加载 ${count.toLocaleString()} 位诗人...`
})

const loadNextChunk = async () => {
  if (isPaused.value || isLoadingChunk.value) return
  
  const currentLoaded = loadedChunkCount.value
  if (currentLoaded >= (totalChunks.value || 0)) return
  
  isLoadingChunk.value = true
  try {
    const nextChunkId = currentLoaded
    const chunkAuthors = await getAuthorsByChunk(nextChunkId)
    loadedAuthors.value.push(...chunkAuthors)
    loadedAuthors.value.sort((a, b) => b.poem_count - a.poem_count)
    loadProgress.value = Math.round(((nextChunkId + 1) / (totalChunks.value || 1)) * 100)
  } catch (e) {
    console.error('Error loading chunk:', e)
  } finally {
    isLoadingChunk.value = false
  }
}

const keepLoadingNextChunk = async () => {
  if (isPaused.value || isLoadingChunk.value) return
  
  while (!isPaused.value && hasMoreChunks.value) {
    await loadNextChunk()
    // 添加小延迟避免阻塞UI
    await new Promise(resolve => setTimeout(resolve, 100))
  }
}

const togglePause = () => {
  isPaused.value = !isPaused.value
  if (!isPaused.value && hasMoreChunks.value) {
    keepLoadingNextChunk()
  }
}

const loadData = async () => {
  isLoadingInitial.value = true
  try {
    await loadMetadata()
    await loadNextChunk()
  } catch (e) {
    console.error('Error loading authors:', e)
  } finally {
    isLoadingInitial.value = false
  }
}

const handleScroll = () => {
  if (!listContainerRef.value || isPaused.value || isLoadingChunk.value) return
  
  const container = listContainerRef.value
  const scrollBottom = container.scrollTop + container.clientHeight
  const threshold = container.scrollHeight - 200
  
  if (scrollBottom >= threshold && hasMoreChunks.value) {
    loadNextChunk()
  }
}

const goToAuthorDetail = (author: AuthorStats) => {
  router.push(`/authors/${encodeURIComponent(author.author)}`)
}

onMounted(() => {
  loadData()
  if (listContainerRef.value) {
    listContainerRef.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  if (listContainerRef.value) {
    listContainerRef.value.removeEventListener('scroll', handleScroll)
  }
})

watch(searchQuery, () => {
  currentPage.value = 1
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
          label="已加载诗人" v-if="dynamicStats.total > 0"
          :value="dynamicStats.total"
          :prefix-icon="PersonOutline"
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

    <NCard v-if="hasMoreChunks || isLoadingInitial" class="loading-card">
      <div class="loading-header">
        <span class="loading-title">{{ loadingHint }}</span>
        <span class="loading-count">
          {{ loadedAuthors.length.toLocaleString() }} 位诗人 / {{ totalAuthorsCount?.toLocaleString() || '...' }} 位
          <span class="chunk-progress" v-if="totalChunks > 0">
            · {{ loadProgress }}%
          </span>
        </span>
      </div>
      <NProgress
        type="line"
        :percentage="loadProgress"
        :indicator-placement="'inside'"
        status="success"
        :height="12"
        :border-radius="6"
        :processing="!isPaused && isLoadingChunk"
      />
      <div class="loading-stats" v-if="loadedAuthors.length > 0">
        <span class="stat-item">已收录诗词: {{ dynamicStats.totalPoems.toLocaleString() }} 首</span>
        <span class="stat-item">当前平均: {{ dynamicStats.average }} 首/人</span>
      </div>
      <div class="loading-actions" v-if="loadedAuthors.length > 0 && !isLoadingInitial">
        <NButton
          v-if="hasMoreChunks"
          :type="isPaused ? 'primary' : 'default'"
          size="small"
          @click="togglePause"
        >
          <template #icon>
            <PlayOutline v-if="isPaused" />
            <PauseOutline v-else />
          </template>
          {{ isPaused ? '继续加载' : '暂停加载' }}
        </NButton>
      </div>
    </NCard>

    <FilterSection class="search-section">
      <NInput
        v-model:value="searchQuery"
        placeholder="搜索诗人..."
        size="large"
        clearable
        style="width: 300px;"
      >
        <template #prefix>
          <SearchOutline />
        </template>
      </NInput>
    </FilterSection>

    <NSpin :show="loading && isLoadingInitial" size="large">
      <NEmpty v-if="!loading && !isLoadingInitial && paginatedAuthors.length === 0" description="暂无数据" />

      <div v-else ref="listContainerRef" class="authors-list-container">
        <div class="authors-list">
          <TransitionGroup name="author-item">
            <div
              v-for="author in paginatedAuthors"
              :key="author.author"
              class="author-card"
              :class="{
                'top-three': author.rank <= 3
              }"
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
                <NProgress
                  type="line"
                  :percentage="item.percentage"
                  :show-indicator="false"
                  :height="6"
                  status="success"
                />
                <span class="type-count">{{ item.count }}</span>
              </div>
            </div>

            <ChevronForwardOutline class="arrow-icon" />
          </div>
          </TransitionGroup>
        </div>
        
        <div v-if="hasMoreChunks && !isLoadingInitial" class="load-more-hint">
          <NSpin v-if="!isPaused" :show="isLoadingChunk" size="small">
            <span class="hint-text">
              {{ isLoadingChunk ? '正在加载更多诗人...' : '向下滚动加载更多' }}
            </span>
          </NSpin>
          <span v-else class="hint-text paused">⏸️ 已暂停加载</span>
        </div>
      </div>
    </NSpin>

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

.stat-card {
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card.stat-updating {
  animation: pulse-bg 1.5s ease-in-out infinite;
}

@keyframes pulse-bg {
  0%, 100% { background-color: #fff; }
  50% { background-color: #f0f7ff; }
}

.loading-card {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.loading-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.loading-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.loading-count {
  font-size: 14px;
  color: #8b2635;
  font-weight: 600;
}

.chunk-progress {
  color: #666;
  font-weight: 400;
}

.loading-stats {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
}

.loading-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
}

.stat-item {
  font-size: 13px;
  color: #666;
}

.search-section {
  margin-bottom: 24px;
}

.authors-list-container {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 8px;
}

.authors-list-container::-webkit-scrollbar {
  width: 6px;
}

.authors-list-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.authors-list-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.authors-list-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.authors-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.load-more-hint {
  text-align: center;
  padding: 24px;
  color: #999;
  font-size: 14px;
}

.load-more-hint .hint-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.load-more-hint .hint-text.paused {
  color: #8b7355;
}

.author-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  cursor: pointer;
}

.author-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.author-card:hover .arrow-icon {
  opacity: 1;
  color: #8b2635;
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
  color: #2c3e50;
  margin-bottom: 8px;
}

.author-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-type {
  font-size: 14px;
  color: #666;
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
  color: #666;
  width: 60px;
  flex-shrink: 0;
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
  color: #999;
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
  .author-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .type-distribution {
    width: 100%;
  }

  .loading-stats {
    flex-direction: column;
    gap: 8px;
  }

  .arrow-icon {
    display: none;
  }
}
</style>
