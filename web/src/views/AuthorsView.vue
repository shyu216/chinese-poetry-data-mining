<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import {
  NCard, NSpin, NEmpty, NInput, NSpace, NTag,
  NButton, NPagination, NScrollbar, NStatistic, NGrid, NGridItem,
  NProgress, NDivider, NDrawer, NDrawerContent, NList, NListItem, NThing,
  NAlert, NIcon
} from 'naive-ui'
import {
  TrophyOutline, PersonOutline, BookOutline,
  SearchOutline, MedalOutline, BarChartOutline,
  DownloadOutline
} from '@vicons/ionicons5'
import { useAuthors } from '@/composables/useAuthors'
import type { AuthorStats } from '@/types/author'

const { 
  loadAllAuthors, 
  searchAuthors, 
  getAuthorStats, 
  authors, 
  loading,
  loadedCount,
  totalChunks,
  onIncrementalLoad,
  totalAuthors: totalAuthorsCount,
  abortLoading,
  pauseLoading,
  resumeLoading,
  isPaused
} = useAuthors()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const incrementalAuthors = ref<AuthorStats[]>([])
const loadProgress = ref(0)
const isIncremental = ref(false)
const isLoadingPaused = ref(false)

// Toggle pause/resume loading
const togglePauseLoading = () => {
  if (isLoadingPaused.value) {
    resumeLoading()
    isLoadingPaused.value = false
  } else {
    pauseLoading()
    isLoadingPaused.value = true
  }
}

// Author poems drawer
const showPoemsDrawer = ref(false)
const selectedAuthor = ref<AuthorStats | null>(null)
const authorPoems = ref<any[]>([])
const isLoadingAuthorPoems = ref(false)
const hasPoemCache = ref(false)
const poemsPage = ref(1)
const poemsPageSize = ref(50)

// Check if poems are cached
const checkPoemCache = async () => {
  try {
    const { getCacheStats } = await import('@/composables/usePoemCache')
    const stats = await getCacheStats()
    hasPoemCache.value = stats.chunks > 0
  } catch (e) {
    hasPoemCache.value = false
  }
}

// Open drawer and show author's poem IDs
const openAuthorPoems = async (author: AuthorStats) => {
  selectedAuthor.value = author
  showPoemsDrawer.value = true
  isLoadingAuthorPoems.value = true
  authorPoems.value = []
  poemsPage.value = 1

  // Check cache status first
  await checkPoemCache()

  try {
    if (hasPoemCache.value && author.poem_ids && author.poem_ids.length > 0) {
      // Try to load from cache
      const { getAllCachedPoems } = await import('@/composables/usePoemCache')
      const cachedPoems = await getAllCachedPoems()
      const cachedMap = new Map(cachedPoems.map(p => [p.id, p]))

      // Map poem IDs to cached poems
      authorPoems.value = author.poem_ids.map((id, index) => {
        const cached = cachedMap.get(id)
        return cached || {
          id,
          title: `诗词 #${index + 1}`,
          dynasty: '-',
          genre: '-',
          author: author.author
        }
      })
    } else if (author.poem_ids && author.poem_ids.length > 0) {
      // No cache, show placeholders
      authorPoems.value = author.poem_ids.map((id, index) => ({
        id,
        title: `诗词 #${index + 1}`,
        dynasty: '-',
        genre: '-',
        author: author.author
      }))
    }
  } catch (e) {
    console.error('Error loading author poems:', e)
  } finally {
    isLoadingAuthorPoems.value = false
  }
}

// Paginated poems for display
const paginatedPoems = computed(() => {
  const start = (poemsPage.value - 1) * poemsPageSize.value
  const end = start + poemsPageSize.value
  return authorPoems.value.slice(start, end)
})

const totalPoemsPages = computed(() => 
  Math.ceil(authorPoems.value.length / poemsPageSize.value)
)

// Dynamic stats based on currently loaded data (incremental or full)
const currentAuthorsList = computed(() => {
  return isIncremental.value && incrementalAuthors.value.length > 0
    ? incrementalAuthors.value
    : authors.value
})

// Real-time stats that update as data loads
const dynamicStats = computed(() => {
  const list = currentAuthorsList.value
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

const displayAuthors = computed(() => {
  // Use current list (incremental during loading, full after)
  const source = currentAuthorsList.value
  
  if (!searchQuery.value.trim()) {
    return source
  }
  return searchAuthors(searchQuery.value)
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
  if (rank === 1) return '#FFD700' // Gold
  if (rank === 2) return '#C0C0C0' // Silver
  if (rank === 3) return '#CD7F32' // Bronze
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

// Animation for new items
const newItemRanks = ref<Set<number>>(new Set())

const triggerItemAnimation = (ranks: number[]) => {
  ranks.forEach(rank => newItemRanks.value.add(rank))
  setTimeout(() => {
    ranks.forEach(rank => newItemRanks.value.delete(rank))
  }, 600)
}

// Loading state message
const loadingHint = computed(() => {
  const count = incrementalAuthors.value.length
  if (count === 0) return '🚀 正在连接...'
  if (count === 1) return `🏆 冠军登场：${incrementalAuthors.value[0]?.author}！`
  if (count === 2) return `🥈 亚军揭晓：${incrementalAuthors.value[1]?.author}！`
  if (count === 3) return `🥉 季军出炉：${incrementalAuthors.value[2]?.author}！`
  return `📚 已加载 ${count.toLocaleString()} 位诗人...`
})

onMounted(() => {
  // Subscribe to incremental loading
  const unsubscribe = onIncrementalLoad((newAuthors, progress) => {
    isIncremental.value = true
    incrementalAuthors.value = newAuthors
    loadProgress.value = progress
    
    // Trigger animation for newly loaded items (last batch)
    const prevLength = incrementalAuthors.value.length
    const newCount = newAuthors.length - prevLength
    if (newCount > 0) {
      const newRanks = []
      for (let i = prevLength + 1; i <= newAuthors.length; i++) {
        newRanks.push(i)
      }
      triggerItemAnimation(newRanks)
    }
  })
  
  // Start loading with incremental mode
  loadAllAuthors(true).then(() => {
    isIncremental.value = false
  })
  
  onUnmounted(() => {
    unsubscribe()
    // Abort ongoing loading when leaving page
    abortLoading()
  })
})

watch(searchQuery, () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="authors-view">
    <header class="page-header">
      <h1 class="page-title">
        <TrophyOutline class="title-icon" />
        诗人排行榜
      </h1>
      <p class="page-subtitle">
        收录 {{ dynamicStats.total }} 位诗人，按诗词数量排序
      </p>
    </header>

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <NCard class="stat-card" :class="{ 'stat-updating': isIncremental }">
          <NStatistic label="总收录诗人" :value="dynamicStats.total">
            <template #prefix>
              <PersonOutline style="color: #8b2635;" />
            </template>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card" :class="{ 'stat-updating': isIncremental }">
          <NStatistic label="诗词最多" :value="dynamicStats.topAuthor">
            <template #prefix>
              <MedalOutline style="color: #8b2635;" />
            </template>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card" :class="{ 'stat-updating': isIncremental }">
          <NStatistic label="最高产量" :value="dynamicStats.maxPoems">
            <template #prefix>
              <BookOutline style="color: #8b2635;" />
            </template>
            <template #suffix>
              <span style="font-size: 14px; color: #999;">首</span>
            </template>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card" :class="{ 'stat-updating': isIncremental }">
          <NStatistic 
            label="平均产量" 
            :value="dynamicStats.average"
          >
            <template #prefix>
              <BarChartOutline style="color: #8b2635;" />
            </template>
            <template #suffix>
              <span style="font-size: 14px; color: #999;">首</span>
            </template>
          </NStatistic>
        </NCard>
      </NGridItem>
    </NGrid>

    <!-- Loading Progress - Only show during incremental loading -->
    <NCard v-if="isIncremental" class="loading-card">
      <div class="loading-header">
        <span class="loading-title">{{ loadingHint }}</span>
        <span class="loading-count">{{ incrementalAuthors.length.toLocaleString() }} / {{ totalAuthorsCount?.toLocaleString() || '...' }}</span>
      </div>
      <NProgress
        type="line"
        :percentage="loadProgress"
        :indicator-placement="'inside'"
        status="success"
        :height="12"
        :border-radius="6"
        :processing="!isLoadingPaused"
      />
      <div class="loading-controls">
        <NButton 
          size="small" 
          :type="isLoadingPaused ? 'primary' : 'default'"
          @click="togglePauseLoading"
        >
          <template #icon>
            <span v-if="isLoadingPaused">▶️</span>
            <span v-else>⏸️</span>
          </template>
          {{ isLoadingPaused ? '继续加载' : '暂停加载' }}
        </NButton>
      </div>
      <div class="loading-stats" v-if="incrementalAuthors.length > 0">
        <span class="stat-item">已收录诗词: {{ dynamicStats.totalPoems.toLocaleString() }} 首</span>
        <span class="stat-item">当前平均: {{ dynamicStats.average }} 首/人</span>
      </div>
    </NCard>

    <NCard class="search-card">
      <NInput
        v-model:value="searchQuery"
        placeholder="搜索诗人..."
        size="large"
        clearable
      >
        <template #prefix>
          <SearchOutline />
        </template>
      </NInput>
    </NCard>

    <NSpin :show="loading && !isIncremental" size="large">
      <NEmpty v-if="!loading && paginatedAuthors.length === 0" description="暂无数据" />
      
      <div v-else class="authors-list">
        <TransitionGroup name="author-item">
          <div
            v-for="author in paginatedAuthors"
            :key="author.author"
            class="author-card"
            :class="{ 
              'top-three': author.rank <= 3,
              'is-new': newItemRanks.has(author.rank)
            }"
            @click="openAuthorPoems(author)"
            style="cursor: pointer;"
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
          </div>
        </TransitionGroup>
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

    <!-- Author Poems Drawer -->
    <NDrawer
      v-model:show="showPoemsDrawer"
      :width="600"
      placement="right"
    >
      <NDrawerContent
        :title="selectedAuthor ? `${selectedAuthor.author} 的诗词 (${authorPoems.length.toLocaleString()}首)` : '诗词列表'"
        closable
      >
        <NSpin :show="isLoadingAuthorPoems" size="large">
          <NEmpty v-if="!isLoadingAuthorPoems && authorPoems.length === 0" description="暂无诗词数据" />
          <div v-else>
            <!-- No Cache Warning -->
            <NAlert
              v-if="!hasPoemCache"
              type="warning"
              :show-icon="true"
              class="cache-warning"
            >
              <template #header>诗词数据未加载</template>
              <p>当前显示的是诗词占位符。要查看完整的诗词标题和内容，请先前往诗词页面加载数据。</p>
              <div class="cache-warning-action">
                <NButton type="primary" @click="$router.push('/poems')">
                  <template #icon>
                    <NIcon><DownloadOutline /></NIcon>
                  </template>
                  前往加载诗词数据
                </NButton>
              </div>
            </NAlert>

            <NList>
              <NListItem v-for="poem in paginatedPoems" :key="poem.id">
                <NThing>
                  <template #header>
                    <span class="poem-title">{{ poem.title }}</span>
                  </template>
                  <template #description>
                    <div class="poem-meta">
                      <NTag v-if="poem.dynasty !== '-'" size="small" type="info">{{ poem.dynasty }}</NTag>
                      <NTag v-if="poem.genre !== '-'" size="small" type="success">{{ poem.genre }}</NTag>
                      <NTag v-if="!hasPoemCache" size="small" type="default">ID: {{ poem.id.slice(0, 8) }}...</NTag>
                    </div>
                  </template>
                </NThing>
              </NListItem>
            </NList>
            <div class="poems-pagination" v-if="totalPoemsPages > 1">
              <NPagination
                v-model:page="poemsPage"
                :page-count="totalPoemsPages"
                :page-size="poemsPageSize"
                show-size-picker
                :page-sizes="[20, 50, 100]"
                @update:page-size="poemsPageSize = $event"
              />
            </div>
          </div>
        </NSpin>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.authors-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
  color: #8b2635;
}

.page-subtitle {
  font-size: 16px;
  color: #666;
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

.loading-controls {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

.loading-stats {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
}

.stat-item {
  font-size: 13px;
  color: #666;
}

.search-card {
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
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.author-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.author-card.top-three {
  background: linear-gradient(135deg, #fff 0%, #fdf6f0 100%);
  border: 1px solid #e8d5c4;
}

.author-card.is-new {
  animation: slideIn 0.6s ease-out;
}

@keyframes slideIn {
  0% {
    opacity: 0;
    transform: translateX(-30px) scale(0.95);
  }
  50% {
    transform: translateX(5px) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
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

.pagination-wrapper {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

/* Poem Drawer Styles */
.poem-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.poem-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.poems-pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.cache-warning {
  margin-bottom: 16px;
}

.cache-warning p {
  margin: 8px 0;
  line-height: 1.5;
}

.cache-warning-action {
  margin-top: 12px;
}

/* Transition Group Animations */
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
}
</style>
