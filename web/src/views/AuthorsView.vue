<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NSpin, NEmpty, NInput, NSpace, NTag,
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
import type { AuthorStats } from '@/types/author'
import PageHeader from '@/components/PageHeader.vue'
import FilterSection from '@/components/FilterSection.vue'
import StatsCard from '@/components/StatsCard.vue'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'

const router = useRouter()
const {
  totalAuthors: totalAuthorsCount,
  totalChunks,
  loading: metadataLoading,
  loadMetadata,
  loadAuthorChunk
} = useAuthorsV2()

const chunkLoader = useChunkLoader()

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
  if (!searchQuery.value.trim()) {
    return loadedAuthors.value
  }
  const query = searchQuery.value.toLowerCase()
  return loadedAuthors.value.filter(a =>
    a.author.toLowerCase().includes(query)
  )
})

const displayAuthors = computed(() => filteredAuthors.value)

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
  const meta = await getMetadata(AUTHORS_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  // 更新缓存的 chunk 数量
  cachedChunksCount.value = loadedChunkIds.length

  if (loadedChunkIds.length === 0) {
    return []
  }

  // 从 IndexedDB 读取每个 chunk 的数据
  const cachedAuthors: AuthorStats[] = []
  for (const chunkId of loadedChunkIds) {
    const chunkData = await getChunkedCache<AuthorStats[]>(AUTHORS_STORAGE, chunkId)
    if (chunkData) {
      cachedAuthors.push(...chunkData)
    }
  }

  if (cachedAuthors.length > 0) {
    loadedAuthors.value = cachedAuthors.sort((a, b) => b.poem_count - a.poem_count)
  }

  return loadedChunkIds
}

const loadData = async () => {
  isInitializing.value = true
  try {
    await loadMetadata()
    const totalChunksCount = totalChunks.value || 0

    // 首先从 IndexedDB 加载缓存的数据
    const loadedChunkIds = await loadCachedChunks()

    // 只加载未加载的 chunk
    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))

    if (unloadedChunkIds.length === 0) {
      hasMoreChunks.value = false
      return
    }

    await chunkLoader.loadChunks<AuthorStats[]>(unloadedChunkIds, loadAuthorChunk, {
      chunkDelay: 150,
      onChunkLoaded: (_, authors) => {
        const authorsArray = authors as AuthorStats[]
        loadedAuthors.value.push(...authorsArray)
        loadedAuthors.value.sort((a, b) => b.poem_count - a.poem_count)
      },
      onComplete: () => {
        hasMoreChunks.value = false
      }
    })
  } finally {
    isInitializing.value = false
  }
}

const goToAuthorDetail = (author: AuthorStats) => {
  router.push(`/authors/${encodeURIComponent(author.author)}`)
}

onMounted(() => {
  loadData()
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

    <NSpin :show="isInitializing && loadedAuthors.length === 0" size="large">
      <NEmpty v-if="!isInitializing && loadedAuthors.length === 0" description="暂无数据" />

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
