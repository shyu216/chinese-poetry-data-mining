<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NCard, NSpin, NEmpty, NInput, NSpace, NTag,
  NButton, NPagination, NScrollbar, NStatistic, NGrid, NGridItem,
  NProgress, NDivider, NAvatar
} from 'naive-ui'
import {
  TrophyOutline, PersonOutline, BookOutline,
  SearchOutline, MedalOutline, BarChartOutline
} from '@vicons/ionicons5'
import { useAuthors } from '@/composables/useAuthors'
import type { AuthorStats } from '@/types/author'

const { loadAllAuthors, searchAuthors, getAuthorStats, authors, loading } = useAuthors()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const stats = computed(() => getAuthorStats())

const filteredAuthors = computed(() => {
  if (!searchQuery.value.trim()) {
    return authors.value
  }
  return searchAuthors(searchQuery.value)
})

const paginatedAuthors = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAuthors.value.slice(start, end).map((author, index) => ({
    ...author,
    rank: start + index + 1
  }))
})

const totalPages = computed(() => Math.ceil(filteredAuthors.value.length / pageSize.value))

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
  return entries.sort((a, b) => b[1] - a[1])[0][0]
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

onMounted(() => {
  loadAllAuthors()
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
        收录 {{ stats.total }} 位诗人，按诗词数量排序
      </p>
    </header>

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="总收录诗人" :value="stats.total">
            <template #prefix>
              <PersonOutline style="color: #8b2635;" />
            </template>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="诗词最多" :value="stats.topAuthor">
            <template #prefix>
              <MedalOutline style="color: #8b2635;" />
            </template>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="最高产量" :value="stats.maxPoems">
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
        <NCard class="stat-card">
          <NStatistic label="平均产量" :value="Math.round(authors.reduce((a, b) => a + b.poem_count, 0) / (authors.length || 1))">
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

    <NSpin :show="loading" size="large">
      <NEmpty v-if="!loading && paginatedAuthors.length === 0" description="暂无数据" />
      
      <div v-else class="authors-list">
        <div
          v-for="author in paginatedAuthors"
          :key="author.author"
          class="author-card"
          :class="{ 'top-three': author.rank <= 3 }"
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

@media (max-width: 768px) {
  .author-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .type-distribution {
    width: 100%;
  }
}
</style>
