<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { getMetadata, getChunkedCache } from '@/composables/useCacheV2'
import { POEMS_STORAGE } from '@/composables/useMetadataLoader'
import type { PoemSummary, PoemFilter } from '@/composables/types'
import {
  NCard, NSpin, NEmpty, NSelect, NSpace, NTag,
  NButton, NInput, NPagination, NGrid, NGridItem
} from 'naive-ui'
import {
  BookOutline, FilterOutline, SearchOutline,
  ChevronForwardOutline, TimeOutline, PersonOutline,
  DownloadOutline
} from '@vicons/ionicons5'
import PageHeader from '@/components/PageHeader.vue'
import FilterSection from '@/components/FilterSection.vue'
import StatsCard from '@/components/StatsCard.vue'
import DynastyBadge from '@/components/DynastyBadge.vue'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'

const router = useRouter()
const {
  metadata,
  totalPoems,
  totalChunks,
  dynasties,
  genres,
  indexLoading,
  loadMetadata,
  loadChunkSummaries,
  queryPoems
} = usePoemsV2()

const chunkLoader = useChunkLoader()

const poems = ref<PoemSummary[]>([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = ref(24)
const searchQuery = ref('')
const isInitializing = ref(true)
const cachedChunksCount = ref(0) // 从 IndexedDB 缓存的 chunk 数量

const dynastyFilter = ref<string | null>(null)
const genreFilter = ref<string | null>(null)

const globalTotal = computed(() => totalPoems.value || 0)
const totalChunksCount = computed(() => totalChunks.value || 0)

const dynastyOptions = computed(() => [
  { label: '全部朝代', value: '' },
  ...dynasties.value.map(d => ({ label: d, value: d }))
])

const genreOptions = computed(() => [
  { label: '全部体裁', value: '' },
  ...genres.value.map(g => ({ label: g, value: g }))
])

// 总的已加载数量 = 缓存的 + 本次加载的
const loadedChunksCount = computed(() => cachedChunksCount.value + chunkLoader.loadedCount.value)
// 还有更多的条件是：总的已加载 < 总数
const hasMoreChunks = computed(() => loadedChunksCount.value < totalChunksCount.value)

const loadingHint = computed(() => {
  const count = poems.value.length
  if (count === 0) return '🚀 正在连接...'
  return `📚 已加载 ${count.toLocaleString()} 首诗词...`
})

const loadPoemsFromLoadedChunks = async () => {
  const filter: PoemFilter = {}

  if (dynastyFilter.value) {
    filter.dynasty = dynastyFilter.value
  }
  if (genreFilter.value) {
    filter.genre = genreFilter.value
  }
  if (searchQuery.value.trim()) {
    filter.search = searchQuery.value
  }

  const result = await queryPoems(filter, page.value, pageSize.value)
  poems.value = result.poems
  totalCount.value = result.filteredTotal
}

// 从 IndexedDB 加载缓存的 chunk 数据
const loadCachedChunks = async (): Promise<number[]> => {
  const meta = await getMetadata(POEMS_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  // 更新缓存的 chunk 数量
  cachedChunksCount.value = loadedChunkIds.length

  if (loadedChunkIds.length === 0) {
    return []
  }

  // 从 IndexedDB 读取每个 chunk 的数据到内存缓存
  for (const chunkId of loadedChunkIds) {
    const chunkData = await getChunkedCache<PoemSummary[]>(POEMS_STORAGE, chunkId)
    if (chunkData) {
      // 数据已经被加载到内存缓存中，queryPoems 会使用这些缓存
    }
  }

  return loadedChunkIds
}

const loadData = async () => {
  isInitializing.value = true
  try {
    await loadMetadata()
    const totalChunksNum = totalChunks.value || 0

    // 首先从 IndexedDB 加载缓存的数据到内存
    const loadedChunkIds = await loadCachedChunks()

    // 立即查询并显示已缓存的数据
    if (loadedChunkIds.length > 0) {
      await loadPoemsFromLoadedChunks()
    }

    // 只加载未加载的 chunk
    const allChunkIds = Array.from({ length: totalChunksNum }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))

    if (unloadedChunkIds.length === 0) {
      return
    }

    await chunkLoader.loadChunks<PoemSummary[]>(unloadedChunkIds, loadChunkSummaries, {
      chunkDelay: 150,
      onChunkLoaded: () => {
        // 每加载一个 chunk，更新显示
        loadPoemsFromLoadedChunks()
      },
      onComplete: () => {
        loadPoemsFromLoadedChunks()
      }
    })
  } finally {
    isInitializing.value = false
  }
}

onMounted(async () => {
  try {
    await loadData()
  } catch (e) {
    console.error(e)
    isInitializing.value = false
  }
})

watch([dynastyFilter, genreFilter], () => {
  page.value = 1
  loadPoemsFromLoadedChunks()
})

const handleSearch = () => {
  page.value = 1
  loadPoemsFromLoadedChunks()
}

const handlePageChange = async (p: number) => {
  page.value = p
  await loadPoemsFromLoadedChunks()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  page.value = 1
  loadPoemsFromLoadedChunks()
}

const goToPoem = (id: string) => {
  router.push(`/poems/${id}`)
}

const clearFilters = () => {
  dynastyFilter.value = null
  genreFilter.value = null
  searchQuery.value = ''
  page.value = 1
  loadPoemsFromLoadedChunks()
}

const isLoading = computed(() => indexLoading.value || (chunkLoader.isLoading.value && poems.value.length === 0))
</script>

<template>
  <div class="poems-view">
    <PageHeader
      title="翰墨集珍"
      subtitle="浏览三十三万首诗词，按朝代、体裁筛选"
      :icon="BookOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard
          label="总收录"
          :value="globalTotal.toLocaleString()"
          :prefix-icon="BookOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="已加载分块"
          :value="`${loadedChunksCount}/${totalChunksCount}`"
          :prefix-icon="DownloadOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="已加载诗词"
          :value="poems.length.toLocaleString()"
          :prefix-icon="TimeOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="加载进度"
          :value="`${Math.round((loadedChunksCount / (totalChunksCount || 1)) * 100)}%`"
          trend="up"
          :prefix-icon="PersonOutline"
        />
      </NGridItem>
    </NGrid>

    <ChunkLoaderStatus
      v-if="chunkLoader.isLoading.value || cachedChunksCount > 0"
      :is-loading="chunkLoader.isLoading.value"
      :is-paused="chunkLoader.isPaused.value"
      :progress="Math.round((loadedChunksCount / (totalChunksCount || 1)) * 100)"
      :loaded-count="loadedChunksCount"
      :total-count="totalChunksCount"
      title="加载诗词数据"
      :hint="loadingHint"
      :stats="[
        { label: '已收录诗词', value: globalTotal.toLocaleString() + ' 首' },
        { label: '当前显示', value: poems.length.toLocaleString() + ' 首' }
      ]"
      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
    />

    <FilterSection class="filters-section">
      <NSpace align="center" :size="12">
        <NSelect
          v-model:value="dynastyFilter"
          :options="dynastyOptions"
          placeholder="朝代"
          style="width: 130px"
          size="medium"
          clearable
        />
        <NSelect
          v-model:value="genreFilter"
          :options="genreOptions"
          placeholder="体裁"
          style="width: 130px"
          size="medium"
          clearable
        />
        <NInput
          v-model:value="searchQuery"
          placeholder="搜索标题或作者..."
          style="width: 220px"
          size="medium"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <SearchOutline style="opacity: 0.5" />
          </template>
        </NInput>
        <NButton
          type="primary"
          size="medium"
          @click="handleSearch"
          :loading="isLoading"
        >
          <template #icon>
            <FilterOutline />
          </template>
          筛选
        </NButton>
        <NButton
          v-if="dynastyFilter || genreFilter || searchQuery"
          size="medium"
          @click="clearFilters"
        >
          清除
        </NButton>
      </NSpace>
    </FilterSection>

    <NSpin :show="isInitializing && poems.length === 0" size="large">
      <NEmpty
        v-if="!isInitializing && poems.length === 0"
        :description="hasMoreChunks ? '加载更多数据可能会有结果' : '未找到符合条件的诗词'"
      >
        <template #extra>
          <NSpace v-if="hasMoreChunks" justify="center">
            <NButton @click="clearFilters">
              清除筛选
            </NButton>
          </NSpace>
          <NButton v-else @click="clearFilters">
            清除筛选
          </NButton>
        </template>
      </NEmpty>

      <div v-else class="poems-container">
        <div class="poems-grid">
          <article
            v-for="poem in poems"
            :key="poem.id"
            class="poem-card"
            @click="goToPoem(poem.id)"
          >
            <div class="card-main">
              <DynastyBadge :dynasty="poem.dynasty" size="small" />
              <div class="poem-info">
                <h3 class="poem-title">{{ poem.title || '无题' }}</h3>
                <div class="poem-subtitle">
                  <span class="author">{{ poem.author }}</span>
                  <span class="divider">·</span>
                  <span class="genre">{{ poem.genre }}</span>
                </div>
              </div>
              <ChevronForwardOutline class="arrow-icon" />
            </div>
          </article>
        </div>

        <div class="pagination-wrapper">
          <NPagination
            :page="page"
            :page-count="Math.ceil(totalCount / pageSize)"
            :page-sizes="[12, 24, 48, 96]"
            :page-size="pageSize"
            show-size-picker
            show-quick-jumper
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </div>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.poems-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.stats-grid {
  margin-bottom: 24px;
}

.filters-section {
  margin-bottom: 24px;
}

.poems-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.poems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
}

.poem-card {
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.poem-card:hover {
  border-color: var(--color-seal, #8b2635);
  background: rgba(139, 38, 53, 0.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.poem-card:hover .arrow-icon {
  opacity: 1;
  color: var(--color-seal, #8b2635);
  transform: translateX(2px);
}

.card-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.poem-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.poem-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.poem-subtitle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.poem-subtitle .author {
  color: var(--color-seal, #8b2635);
  font-weight: 500;
}

.poem-subtitle .divider {
  opacity: 0.5;
}

.poem-subtitle .genre {
  opacity: 0.8;
}

.arrow-icon {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  color: var(--color-ink-light, #999);
  opacity: 0;
  transition: all 0.2s ease;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
}

@media (max-width: 768px) {
  .poems-view {
    padding: 16px;
  }

  .poems-grid {
    grid-template-columns: 1fr;
  }

  .filters-section :deep(.n-space) {
    flex-wrap: wrap;
  }

  .filters-section .n-select,
  .filters-section .n-input {
    width: 100% !important;
  }
}
</style>
