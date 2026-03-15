<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePoems, type PoemSummary } from '@/composables/usePoems'
import { 
  NCard, NSpin, NEmpty, NSelect, NSpace, NTag, 
  NButton, NInput, NPagination, NScrollbar 
} from 'naive-ui'
import { 
  BookOutline, FilterOutline, SearchOutline,
  ChevronForwardOutline, TimeOutline, PersonOutline,
  DownloadOutline
} from '@vicons/ionicons5'

const router = useRouter()
const { getStats, loadChunkSummaries, loadIndex, restoreCachedChunks, loading, loadingChunk } = usePoems()

const poems = ref<PoemSummary[]>([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = ref(24)
const searchQuery = ref('')

// Track loaded chunks for "load more" functionality
const loadedChunkIds = ref<number[]>([])
const totalChunksCount = ref(0)

const dynastyFilter = ref<string | null>(null)
const genreFilter = ref<string | null>(null)

const availableDynasties = ref<string[]>([])
const availableGenres = ref<string[]>([])
const globalTotal = ref(332712)

const dynastyOptions = computed(() => [
  { label: '全部朝代', value: '' },
  ...availableDynasties.value.map(d => ({ label: d, value: d }))
])

const genreOptions = computed(() => [
  { label: '全部体裁', value: '' },
  ...availableGenres.value.map(g => ({ label: g, value: g }))
])

onMounted(async () => {
  try {
    // First restore cached chunks from IndexedDB
    const cachedChunkIds = await restoreCachedChunks()
    loadedChunkIds.value = cachedChunkIds
    
    const stats = await getStats()
    availableDynasties.value = stats.dynasties
    availableGenres.value = stats.genres
    globalTotal.value = stats.total
    totalChunksCount.value = stats.chunks
    
    // If no cached chunks, do initial load
    if (loadedChunkIds.value.length === 0) {
      await initialLoad()
    } else {
      // Use cached chunks
      await loadPoems()
    }
  } catch (e) {
    console.error(e)
  }
})

const loadPoems = async () => {
  // Get all loaded poems from cached chunks
  const allLoadedPoems: PoemSummary[] = []
  for (const chunkId of loadedChunkIds.value) {
    const chunkPoems = await loadChunkSummaries(chunkId)
    allLoadedPoems.push(...chunkPoems)
  }
  
  // Apply filters
  let filtered = allLoadedPoems
  if (dynastyFilter.value) {
    filtered = filtered.filter(p => p.dynasty === dynastyFilter.value)
  }
  if (genreFilter.value) {
    filtered = filtered.filter(p => p.genre === genreFilter.value)
  }
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p => 
      p.title?.toLowerCase().includes(query) ||
      p.author?.toLowerCase().includes(query)
    )
  }
  
  // Paginate
  const start = (page.value - 1) * pageSize.value
  poems.value = filtered.slice(start, start + pageSize.value)
  totalCount.value = filtered.length
}

watch([dynastyFilter, genreFilter], () => {
  page.value = 1
  loadPoems()
})

const handleSearch = () => {
  page.value = 1
  loadPoems()
}

const isLastPage = computed(() => page.value >= Math.ceil(totalCount.value / pageSize.value))
const isAutoLoading = ref(false)

const handlePageChange = async (p: number) => {
  page.value = p
  await loadPoems()
  
  // Auto load next chunk when reaching last page
  if (isLastPage.value && hasMoreChunks.value && !isAutoLoading.value) {
    isAutoLoading.value = true
    await loadNextChunks()
    isAutoLoading.value = false
  }
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
  loadedChunkIds.value = []
  loadPoems()
}

// Computed properties for load more section
const loadedPoemsCount = computed(() => loadedChunkIds.value.length * 1000)
const loadedChunksCount = computed(() => loadedChunkIds.value.length)
const hasMoreChunks = computed(() => {
  // Check if there are more chunks to load based on filters
  return loadedChunkIds.value.length < totalChunksCount.value
})

// Get relevant chunk IDs based on filters
const getRelevantChunkIds = async (): Promise<number[]> => {
  const index = await loadIndex()
  return index.chunks
    .filter(chunk => {
      if (dynastyFilter.value && !chunk.dynasties.includes(dynastyFilter.value)) return false
      if (genreFilter.value && !chunk.genres.includes(genreFilter.value)) return false
      return true
    })
    .map(c => c.id)
}

// Load next 1 chunk
const loadNextChunks = async () => {
  const relevantChunks = await getRelevantChunkIds()
  
  // Find next chunk to load
  const alreadyLoaded = new Set(loadedChunkIds.value)
  const nextChunkId = relevantChunks.find(id => !alreadyLoaded.has(id))
  
  if (nextChunkId === undefined) return
  
  // Load 1 chunk
  await loadChunkSummaries(nextChunkId)
  loadedChunkIds.value.push(nextChunkId)
  
  // Refresh current page
  await loadPoems()
}

// Initial load - load first chunk
const initialLoad = async () => {
  const relevantChunks = await getRelevantChunkIds()
  if (relevantChunks.length > 0 && loadedChunkIds.value.length === 0) {
    const firstChunkId = relevantChunks[0]
    if (firstChunkId !== undefined) {
      await loadChunkSummaries(firstChunkId)
      loadedChunkIds.value = [firstChunkId]
    }
  }
  await loadPoems()
}
</script>

<template>
  <div class="poets-view">
    <section class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-icon">
            <BookOutline />
          </span>
          翰墨集珍
        </h1>
        <p class="page-desc">
          浏览三十三万首诗词，按朝代、体裁筛选
        </p>
      </div>
      
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-value">{{ globalTotal.toLocaleString() }}</span>
          <span class="stat-label">总收录</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <span class="stat-value">{{ loadedChunksCount }}/{{ totalChunksCount }}</span>
          <span class="stat-label">已加载分块</span>
        </div>
        <div class="stat-divider" v-if="loadedChunksCount < totalChunksCount" />
        <div class="stat-item loading-hint" v-if="loadedChunksCount < totalChunksCount">
          <span class="stat-value">{{ (loadedChunksCount / totalChunksCount * 100).toFixed(1) }}%</span>
          <span class="stat-label">数据量</span>
        </div>
        <div class="stat-actions" v-if="loadedChunksCount < totalChunksCount">
          <NButton 
            size="small" 
            :loading="loadingChunk"
            @click="loadNextChunks"
            class="top-load-btn"
          >
            <template #icon>
              <DownloadOutline />
            </template>
            加载更多
          </NButton>
        </div>
      </div>
    </section>

    <section class="filters-section">
      <div class="filters-row">
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
            :loading="loading || loadingChunk"
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
      </div>
    </section>

    <NSpin :show="loading || loadingChunk" size="large">
      <NEmpty 
        v-if="!loading && !loadingChunk && poems.length === 0" 
        description="未找到符合条件的诗词"
      >
        <template #extra>
          <NButton @click="clearFilters">
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
              <span 
                class="dynasty-badge-compact"
                :style="{ 
                  color: getDynastyConfig(poem.dynasty).color,
                  background: getDynastyConfig(poem.dynasty).bg 
                }"
              >
                {{ poem.dynasty }}
              </span>
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

        <div class="load-more-section" v-if="hasMoreChunks">
          <div v-if="isAutoLoading" class="auto-loading-hint">
            <NSpin size="small" />
            <span>已翻到最后一页，正在自动加载下一批...</span>
          </div>
          <NButton 
            v-else
            size="large" 
            :loading="loadingChunk"
            @click="loadNextChunks"
            class="load-more-btn"
          >
            <template #icon>
              <DownloadOutline />
            </template>
            加载更多诗词 (已加载 {{ loadedPoemsCount.toLocaleString() }} 首)
          </NButton>
          <p class="load-more-hint">
            <span v-if="isLastPage" class="last-page-tip">💡 提示：翻到最后一页会自动加载下一批</span>
            <span v-else>每批加载约 1000 首诗词</span>
          </p>
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

.page-header {
  margin-bottom: 24px;
}

.header-content {
  margin-bottom: 16px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px;
  font-family: "Noto Serif SC", serif;
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink);
}

.title-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-seal);
  color: #fff;
  border-radius: 8px;
  font-size: 20px;
}

.page-desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink-light);
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-value {
  font-family: "Noto Serif SC", serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-seal);
}

.stat-label {
  font-size: 13px;
  color: var(--color-ink-light);
}

.stat-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border);
}

.filters-section {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.filters-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
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

.load-more-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 16px;
}

.load-more-btn {
  min-width: 300px;
}

.load-more-hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink-light);
}

.last-page-tip {
  color: var(--color-seal);
  font-weight: 500;
}

.auto-loading-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: rgba(139, 38, 53, 0.05);
  border: 1px dashed var(--color-seal);
  border-radius: 8px;
  color: var(--color-seal);
  font-size: 14px;
}

.loading-hint .stat-value {
  color: #047857;
}

.stat-actions {
  margin-left: auto;
  padding-left: 8px;
  border-left: 1px solid var(--color-border);
}

.top-load-btn {
  font-size: 13px;
}
</style>
