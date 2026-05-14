<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NEmpty, NSpace, NTag, NButton, NPagination, NGrid, NGridItem, NTooltip } from 'naive-ui'
import {
  TrophyOutline,
  PersonOutline,
  BookOutline,
  MedalOutline,
  BarChartOutline,
  ChevronForwardOutline,
  ShuffleOutline,
  RefreshOutline
} from '@vicons/ionicons5'
import { useAuthors } from '@/composables/useAuthors'
import { useAuthorSearch } from '@/search'
import { useShuffle } from '@/composables/useShuffle'
import type { AuthorStats } from '@/types/author'
import { PageHeader } from '@/components/layout'
import { StatsCard, RankBadge, TypeDistribution } from '@/components/display'
import { SearchContainer } from '@/components/search'
import { AuthorClusterViz } from '@/components/author'
import { useAuthorClusters } from '@/composables/useAuthorClusters'
import type { AuthorNode } from '@/types/cluster'

const router = useRouter()
const { totalAuthors: totalAuthorsCount, loadMetadata, queryAuthors } = useAuthors()
const { search: searchAuthors } = useAuthorSearch()
const { loading: clusterLoading, loadClusters, sortedClusters, authorNodes } = useAuthorClusters()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const currentAuthors = ref<AuthorStats[]>([])
const totalResults = ref(0)
const isInitializing = ref(true)
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: 'memory' })

const { isShuffled, shuffledItems, toggleShuffle, shuffle } = useShuffle({ items: computed(() => currentAuthors.value) })
const isSearchMode = computed(() => searchQuery.value.trim().length > 0)
const displayAuthors = computed(() => (isSearchMode.value ? currentAuthors.value : shuffledItems.value))
const displayTotal = computed(() => totalResults.value)
const totalPages = computed(() => Math.max(1, Math.ceil(displayTotal.value / pageSize.value)))
const paginatedAuthors = computed(() => displayAuthors.value.map((author, index) => ({
  ...author,
  rank: (currentPage.value - 1) * pageSize.value + index + 1
})))

const dynamicStats = computed(() => {
  const list = currentAuthors.value
  const top = list[0]
  const totalPoems = list.reduce((sum, item) => sum + item.poem_count, 0)
  return {
    total: displayTotal.value,
    topAuthor: top?.author || '-',
    maxPoems: top?.poem_count || 0,
    average: list.length > 0 ? Math.round(totalPoems / list.length) : 0
  }
})

function getTopPoemType(typeCounts: Record<string, number>) {
  const entries = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])
  return entries[0]?.[0] || '-'
}

function getTypeDistributionData(typeCounts: Record<string, number>) {
  const total = Math.max(1, Object.values(typeCounts).reduce((sum, value) => sum + value, 0))
  return Object.entries(typeCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([type, count]) => ({ type, count, percentage: Math.round((count / total) * 100) }))
}

async function refreshPage() {
  if (isSearchMode.value) {
    isSearching.value = true
    try {
      const result = await searchAuthors(searchQuery.value.trim(), {
        limit: pageSize.value,
        offset: (currentPage.value - 1) * pageSize.value
      })
      currentAuthors.value = result.items
      totalResults.value = result.total
      searchStats.value = { queryTime: result.queryTime, source: result.source }
    } finally {
      isSearching.value = false
    }
    return
  }

  const result = await queryAuthors(undefined, currentPage.value, pageSize.value)
  currentAuthors.value = result.authors
  totalResults.value = result.filteredTotal
  searchStats.value = { queryTime: 0, source: 'memory' }
}

function goToAuthorDetail(author: AuthorStats) {
  router.push(`/authors/${encodeURIComponent(author.author)}`)
}

function onSelectClusterAuthor(author: AuthorNode) {
  router.push(`/authors/${encodeURIComponent(author.name)}`)
}

function onSelectCluster(clusterId: number) {
  console.log('Selected cluster:', clusterId)
}

onMounted(async () => {
  try {
    await loadMetadata()
    await Promise.all([refreshPage(), loadClusters()])
  } finally {
    isInitializing.value = false
  }
})

watch(searchQuery, async () => {
  currentPage.value = 1
  await refreshPage()
})

watch([currentPage, pageSize], async () => {
  if (isInitializing.value) return
  await refreshPage()
})
</script>

<template>
  <div class="authors-view">
    <PageHeader title="诗人列表" :subtitle="`共 ${totalAuthorsCount.toLocaleString()} 位诗人，当前结果 ${displayTotal.toLocaleString()} 位`" :icon="TrophyOutline" />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem><StatsCard label="诗人数量" :value="displayTotal.toLocaleString()" :prefix-icon="PersonOutline" /></NGridItem>
      <NGridItem><StatsCard label="作品最多" :value="dynamicStats.topAuthor" :prefix-icon="MedalOutline" /></NGridItem>
      <NGridItem><StatsCard label="最多作品" :value="dynamicStats.maxPoems" suffix="首" :prefix-icon="BookOutline" /></NGridItem>
      <NGridItem><StatsCard label="当前页平均" :value="dynamicStats.average" suffix="首" :prefix-icon="BarChartOutline" /></NGridItem>
    </NGrid>

    <AuthorClusterViz
      :clusters="sortedClusters"
      :authors="authorNodes"
      :loading="clusterLoading"
      @select-author="onSelectClusterAuthor"
      @select-cluster="onSelectCluster"
    />

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索诗人..."
      :total="displayTotal"
      :query-time="searchStats.queryTime"
      :source="searchStats.source as any"
      :loading="isSearching"
    >
      <template #filters>
        <NSpace>
          <NTooltip trigger="hover">
            <template #trigger>
              <NButton :type="isShuffled ? 'primary' : 'default'" :ghost="!isShuffled" :disabled="isSearchMode" @click="toggleShuffle">
                <template #icon><ShuffleOutline /></template>
                随机
              </NButton>
            </template>
            仅对当前页结果随机排序
          </NTooltip>
          <NTooltip v-if="isShuffled && !isSearchMode" trigger="hover">
            <template #trigger>
              <NButton @click="shuffle">
                <template #icon><RefreshOutline /></template>
                刷新
              </NButton>
            </template>
            重新排序
          </NTooltip>
        </NSpace>
      </template>
    </SearchContainer>

    <NEmpty v-if="isInitializing" description="正在加载诗人数据..." />
    <NEmpty v-else-if="paginatedAuthors.length === 0" description="没有匹配结果" />

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
              <NTag type="primary" size="small">{{ author.poem_count }} 首</NTag>
              <span class="top-type">{{ getTopPoemType(author.poem_type_counts) }}</span>
            </div>
          </div>
          <div class="type-distribution-wrapper">
            <TypeDistribution :data="getTypeDistributionData(author.poem_type_counts)" :show-percentage="false" size="small" />
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
  margin: 0 0 8px;
}

.author-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.top-type {
  color: #666;
  font-size: 14px;
}

.type-distribution-wrapper {
  width: 200px;
}

.arrow-icon {
  opacity: 0.45;
  transition: all 0.2s ease;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
