<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePoemsV2} from '@/composables/usePoemsV2'
import type {
  PoemSummary,
  PoemFilter
} from '@/composables/types'
import { 
  NCard, NSpin, NEmpty, NSelect, NSpace, NTag, 
  NButton, NInput, NPagination, NScrollbar, NGrid, NGridItem 
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

const router = useRouter()
const { 
  metadata, 
  totalPoems, 
  totalChunks, 
  loadedChunkCount, 
  dynasties, 
  genres, 
  indexLoading, 
  loadMetadata,
  loadChunkSummaries,
  queryPoems,
  preloadChunks,
  clearCache
} = usePoemsV2()

const poems = ref<PoemSummary[]>([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = ref(24)
const searchQuery = ref('')

const dynastyFilter = ref<string | null>(null)
const genreFilter = ref<string | null>(null)

const globalTotal = computed(() => totalPoems.value || 0)
const totalChunksCount = computed(() => totalChunks.value || 0)
const loadedChunksCount = computed(() => loadedChunkCount.value || 0)

const dynastyOptions = computed(() => [
  { label: '全部朝代', value: '' },
  ...dynasties.value.map(d => ({ label: d, value: d }))
])

const genreOptions = computed(() => [
  { label: '全部体裁', value: '' },
  ...genres.value.map(g => ({ label: g, value: g }))
])

onMounted(async () => {
  try {
    await loadMetadata()
    await loadPoems()
  } catch (e) {
    console.error(e)
  }
})

const loadPoems = async () => {
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

watch([dynastyFilter, genreFilter], () => {
  page.value = 1
  loadPoems()
})

const handleSearch = () => {
  page.value = 1
  loadPoems()
}

const handlePageChange = async (p: number) => {
  page.value = p
  await loadPoems()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  page.value = 1
  loadPoems()
}

const goToPoem = (id: string) => {
  router.push(`/poems/${id}`)
}

const dynastyConfig: Record<string, { color: string; bg: string; icon: string }> = {
  '唐': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', icon: '盛' },
  '宋': { color: '#1E40AF', bg: 'rgba(30, 64, 175, 0.08)', icon: '雅' },
  '元': { color: '#047857', bg: 'rgba(4, 120, 87, 0.08)', icon: '曲' },
  '明': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', icon: '文' },
  '清': { color: '#7C3AED', bg: 'rgba(124, 58, 237, 0.08)', icon: '韵' },
  '近现代': { color: '#DC2626', bg: 'rgba(220, 38, 38, 0.08)', icon: '新' }
}

const getDynastyConfig = (dynasty: string) => {
  return dynastyConfig[dynasty] || { color: '#5C5244', bg: 'rgba(92, 82, 68, 0.08)', icon: '古' }
}

const clearFilters = () => {
  dynastyFilter.value = null
  genreFilter.value = null
  searchQuery.value = ''
  page.value = 1
  loadPoems()
}

const loadMoreChunks = async () => {
  const currentLoaded = loadedChunkCount.value
  const nextChunkId = currentLoaded
  await preloadChunks([nextChunkId])
  await loadPoems()
}

const hasMoreChunks = computed(() => {
  return loadedChunkCount.value < totalChunks.value
})

const isLoading = computed(() => indexLoading.value)
</script>

<template>
  <div class="poets-view">
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
      <NGridItem v-if="hasMoreChunks">
        <StatsCard
          label="数据量"
          :value="`${(loadedChunksCount / totalChunksCount * 100).toFixed(1)}%`"
          trend="up"
          :prefix-icon="TimeOutline"
        />
      </NGridItem>
      <NGridItem v-if="hasMoreChunks">
        <div class="load-btn-wrapper">
          <NButton 
            type="primary"
            size="medium"
            :loading="isLoading"
            @click="loadMoreChunks"
            block
          >
            <template #icon>
              <DownloadOutline />
            </template>
            加载更多
          </NButton>
        </div>
      </NGridItem>
    </NGrid>

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

    <NSpin :show="isLoading" size="large">
      <NEmpty 
        v-if="!isLoading && poems.length === 0" 
        :description="hasMoreChunks ? '加载更多诗词可能会有结果' : '未找到符合条件的诗词'"
      >
        <template #extra>
          <NSpace v-if="hasMoreChunks" justify="center">
            <NButton type="primary" :loading="isLoading" @click="loadMoreChunks">
              <template #icon>
                <DownloadOutline />
              </template>
              加载更多
            </NButton>
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
            class="poem-card-compact"
            @click="goToPoem(poem.id)"
          >
            <div class="card-main">
              <DynastyBadge :dynasty="poem.dynasty" size="small" />
              <div class="poem-info">
                <h3 class="poem-title-compact">{{ poem.title || '无题' }}</h3>
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
.poets-view {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  margin-bottom: 24px;
}

.load-btn-wrapper {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
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

@media (max-width: 768px) {
  .poems-grid {
    grid-template-columns: 1fr;
  }

  .filters-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filters-row .n-space {
    flex-wrap: wrap;
  }

  .filters-row .n-select,
  .filters-row .n-input {
    width: 100% !important;
  }

  .stats-bar {
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 16px;
  }

  .stat-item {
    min-width: auto;
  }

  .stat-divider {
    display: none;
  }
}

.poem-card-compact {
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.poem-card-compact:hover {
  border-color: var(--color-seal);
  background: rgba(139, 38, 53, 0.02);
}

.card-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dynasty-badge-compact {
  flex-shrink: 0;
  min-width: 32px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
  text-align: center;
}

.poem-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.poem-title-compact {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
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
  color: var(--color-ink-light);
}

.poem-subtitle .author {
  color: var(--color-seal);
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
  color: var(--color-ink-light);
  opacity: 0;
  transition: all 0.2s ease;
}

.poem-card-compact:hover .arrow-icon {
  opacity: 1;
  color: var(--color-seal);
  transform: translateX(2px);
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}
</style>
