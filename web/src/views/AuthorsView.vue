<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import {
  NCard, NSpin, NEmpty, NInput, NSpace, NTag,
  NButton, NPagination, NScrollbar, NStatistic, NGrid, NGridItem,
  NProgress, NDivider
} from 'naive-ui'
import {
  TrophyOutline, PersonOutline, BookOutline,
  SearchOutline, MedalOutline, BarChartOutline
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
  abortLoading
} = useAuthors()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const incrementalAuthors = ref<AuthorStats[]>([])
const loadProgress = ref(0)
const isIncremental = ref(false)

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
  if (count < 10) return `✨ 前十名加载中... (${count}/10)`
  if (count < 50) return `📚 前五十名加载中... (${count}/50)`
  if (count < 100) return `📖 前一百名加载中... (${count}/100)`
  return `📚 已加载 ${count} 位诗人...`
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
        <span class="loading-count">{{ incrementalAuthors.length }} / {{ totalAuthorsCount || '...' }}</span>
      </div>
      <NProgress
        type="line"
        :percentage="loadProgress"
        :indicator-placement="'inside'"
        status="success"
        :height="12"
        :border-radius="6"
        :processing="true"
      />
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
