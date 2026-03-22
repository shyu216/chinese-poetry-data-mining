<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { getMetadata, getChunkedCache } from '@/composables/useCacheV2'
import { POEMS_STORAGE } from '@/composables/useMetadataLoader'
import { usePoemSearch } from '@/search'
import type { PoemSummary, PoemFilter } from '@/composables/types'
import {
  NCard, NEmpty, NSelect, NSpace, NTag,
  NButton, NInput, NPagination, NGrid, NGridItem
} from 'naive-ui'
import {
  BookOutline, FilterOutline, SearchOutline,
  ChevronForwardOutline, TimeOutline, PersonOutline,
  DownloadOutline, LibraryOutline, FlameOutline,
  SchoolOutline, MusicalNotesOutline
} from '@vicons/ionicons5'
import PageHeader from '@/components/PageHeader.vue'
import FilterSection from '@/components/FilterSection.vue'
import StatsCard from '@/components/StatsCard.vue'
import DynastyBadge from '@/components/DynastyBadge.vue'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'
import { SearchContainer } from '@/components/search'
import { useLoading } from '@/composables/useLoading'

const router = useRouter()
const globalLoading = useLoading()
const {
  metadata,
  totalPoems,
  totalChunks,
  dynasties,
  genres,
  poemCounts,
  indexLoading,
  loadMetadata,
  loadChunkSummaries,
  queryPoems
} = usePoemsV2()

const chunkLoader = useChunkLoader()

// 新的诗词搜索模块
const { search: searchPoems, isReady: poemSearchReady } = usePoemSearch()
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: '' })

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

// 实时统计已加载的诗词数量（按朝代和体裁）
const loadedPoemStats = ref({
  total: 0,
  tangshi: 0,
  songshi: 0,
  songci: 0
})

// 计算实时数量：如果已全部加载则显示总数，否则显示已加载数
const displayTotal = computed(() => {
  const isFullyLoaded = loadedChunksCount.value >= totalChunksCount.value && totalChunksCount.value > 0
  return isFullyLoaded ? globalTotal.value : loadedPoemStats.value.total
})

const displayTangshi = computed(() => {
  const isFullyLoaded = loadedChunksCount.value >= totalChunksCount.value && totalChunksCount.value > 0
  return isFullyLoaded ? poemCounts.value.tangshi : loadedPoemStats.value.tangshi
})

const displaySongshi = computed(() => {
  const isFullyLoaded = loadedChunksCount.value >= totalChunksCount.value && totalChunksCount.value > 0
  return isFullyLoaded ? poemCounts.value.songshi : loadedPoemStats.value.songshi
})

const displaySongci = computed(() => {
  const isFullyLoaded = loadedChunksCount.value >= totalChunksCount.value && totalChunksCount.value > 0
  return isFullyLoaded ? poemCounts.value.songci : loadedPoemStats.value.songci
})

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
  const count = displayTotal.value
  if (count === 0) return '🚀 正在连接...'
  return `📚 已加载 ${count.toLocaleString()} 首诗词...`
})

const loadPoemsFromLoadedChunks = async () => {
  const query = searchQuery.value.trim()
  
  // 如果有搜索关键词，使用新的 PoemSearch
  if (query && poemSearchReady.value) {
    isSearching.value = true
    try {
      const result = await searchPoems(query, {
        limit: pageSize.value,
        offset: (page.value - 1) * pageSize.value,
        filters: {
          dynasty: dynastyFilter.value || undefined,
          genre: genreFilter.value || undefined
        }
      })
      poems.value = result.items
      totalCount.value = result.total
      searchStats.value = { queryTime: result.queryTime, source: result.source }
    } finally {
      isSearching.value = false
    }
    return
  }
  
  // 否则使用原有的筛选逻辑
  const filter: PoemFilter = {}

  if (dynastyFilter.value) {
    filter.dynasty = dynastyFilter.value
  }
  if (genreFilter.value) {
    filter.genre = genreFilter.value
  }

  const result = await queryPoems(filter, page.value, pageSize.value)
  poems.value = result.poems
  totalCount.value = result.filteredTotal
}

// 统计诗词数量（按朝代和体裁）
const countPoemsByCategory = (poems: PoemSummary[]) => {
  let tangshi = 0
  let songshi = 0
  let songci = 0
  let total = 0

  for (const poem of poems) {
    total++
    if (poem.dynasty === '唐' && poem.genre === '诗') {
      tangshi++
    } else if (poem.dynasty === '宋' && poem.genre === '诗') {
      songshi++
    } else if (poem.dynasty === '宋' && poem.genre === '词') {
      songci++
    }
  }

  return { tangshi, songshi, songci, total }
}

// 从 IndexedDB 加载缓存的 chunk 数据
const loadCachedChunks = async (): Promise<number[]> => {
  console.log('[PoemsView] 🔄 开始加载本地缓存...')
  const startTime = performance.now()

  const meta = await getMetadata(POEMS_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  // 更新缓存的 chunk 数量
  cachedChunksCount.value = loadedChunkIds.length
  console.log(`[PoemsView] 📦 发现 ${loadedChunkIds.length} 个缓存分块`)

  if (loadedChunkIds.length === 0) {
    console.log('[PoemsView] ⚠️ 无缓存数据，将从服务器加载')
    return []
  }

  // 从 IndexedDB 读取每个 chunk 的数据并统计
  let totalCount = 0
  let totalTangshi = 0
  let totalSongshi = 0
  let totalSongci = 0

  console.log(`[PoemsView] 📖 开始读取 ${loadedChunkIds.length} 个缓存分块...`)
  for (const chunkId of loadedChunkIds) {
    const chunkStartTime = performance.now()
    const chunkData = await getChunkedCache<PoemSummary[]>(POEMS_STORAGE, chunkId)
    const chunkDuration = Math.round(performance.now() - chunkStartTime)

    if (chunkData) {
      totalCount += chunkData.length
      const counts = countPoemsByCategory(chunkData)
      totalTangshi += counts.tangshi
      totalSongshi += counts.songshi
      totalSongci += counts.songci
      console.log(`[PoemsView]   ├─ 分块 #${chunkId}: ${chunkData.length} 首诗词 (${chunkDuration}ms)`)
    }
  }

  loadedPoemStats.value = {
    total: totalCount,
    tangshi: totalTangshi,
    songshi: totalSongshi,
    songci: totalSongci
  }

  const totalDuration = Math.round(performance.now() - startTime)
  console.log(`[PoemsView] ✅ 缓存加载完成: ${totalCount} 首诗词 (唐诗:${totalTangshi}, 宋诗:${totalSongshi}, 宋词:${totalSongci}) - ${totalDuration}ms`)

  return loadedChunkIds
}

const loadData = async () => {
  console.log('[PoemsView] 🚀 开始加载数据...')
  const totalStartTime = performance.now()

  // 阶段1：阻塞性加载 - 元数据（必须等待）
  const initTaskId = globalLoading.startBlocking(
    '准备诗词宝库',
    '正在建立数据连接...'
  )

  isInitializing.value = true
  try {
    // 阶段1：加载元数据
    globalLoading.update(initTaskId, { phase: 'meta' })
    console.log('[PoemsView] 📋 阶段1: 加载元数据...')
    const metaStartTime = performance.now()
    await loadMetadata()
    const totalChunksNum = totalChunks.value || 0
    console.log(`[PoemsView] ✅ 元数据加载完成: ${totalPoems.value} 首诗词, ${totalChunksNum} 个分块 - ${Math.round(performance.now() - metaStartTime)}ms`)

    // 阶段2：检查缓存
    globalLoading.update(initTaskId, {
      phase: 'search',
      description: '正在检查本地缓存...',
      progress: 30
    })
    console.log('[PoemsView] 💾 阶段2: 检查本地缓存...')
    const cacheStartTime = performance.now()
    const loadedChunkIds = await loadCachedChunks()
    console.log(`[PoemsView] ✅ 缓存检查完成 - ${Math.round(performance.now() - cacheStartTime)}ms`)

    // 阶段3：UI 准备
    globalLoading.update(initTaskId, {
      phase: 'ui',
      description: '正在调整布局...',
      progress: 50
    })
    console.log('[PoemsView] 🎨 阶段3: 准备UI...')
    const uiStartTime = performance.now()

    // 立即显示已缓存的数据
    if (loadedChunkIds.length > 0) {
      await loadPoemsFromLoadedChunks()
    }
    console.log(`[PoemsView] ✅ UI准备完成 - ${Math.round(performance.now() - uiStartTime)}ms`)

    // 只加载未加载的 chunk
    const allChunkIds = Array.from({ length: totalChunksNum }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))
    console.log(`[PoemsView] 📊 需要加载的分块: ${unloadedChunkIds.length} 个 (已缓存: ${loadedChunkIds.length} 个)`)

    // 完成阻塞性加载
    globalLoading.update(initTaskId, {
      description: '准备就绪',
      progress: 100
    })
    setTimeout(() => globalLoading.finish(initTaskId), 200)

    if (unloadedChunkIds.length === 0) {
      console.log('[PoemsView] ✨ 所有数据已从缓存加载，无需网络请求')
      isInitializing.value = false
      return
    }

    // 阶段4：后台加载剩余数据（不阻塞用户交互）
    console.log('[PoemsView] 🌐 阶段4: 开始后台加载网络数据...')
    const bgStartTime = performance.now()
    const bgTaskId = globalLoading.startBackground(
      '补充诗词数据',
      '正在汇聚千年文脉...'
    )

    let currentLoadedCount = loadedChunkIds.length
    let networkDataCount = 0

    await chunkLoader.loadChunks<PoemSummary[]>(unloadedChunkIds, loadChunkSummaries, {
      concurrency: 5,
      chunkDelay: 0,
      onChunkLoaded: (chunkId, chunk) => {
        // 每加载一个 chunk，更新统计
        if (chunk) {
          const counts = countPoemsByCategory(chunk as PoemSummary[])
          loadedPoemStats.value.tangshi += counts.tangshi
          loadedPoemStats.value.songshi += counts.songshi
          loadedPoemStats.value.songci += counts.songci
          loadedPoemStats.value.total += counts.total
          networkDataCount += (chunk as PoemSummary[]).length
        }
        loadPoemsFromLoadedChunks()

        currentLoadedCount++
        const progress = Math.round((currentLoadedCount / totalChunksNum) * 100)

        // 每加载10%更新一次提示
        if (currentLoadedCount % Math.max(1, Math.floor(totalChunksNum / 10)) === 0) {
          const phases = ['正在读取诗作档案...', '正在整理诗词分类...', '正在汇聚千年文脉...', '正在构建诗词图谱...']
          const phase = phases[Math.floor((currentLoadedCount / totalChunksNum) * phases.length)] || phases[0]
          globalLoading.update(bgTaskId, {
            description: `${phase} (${currentLoadedCount}/${totalChunksNum})`,
            progress,
            current: currentLoadedCount,
            total: totalChunksNum
          })
          console.log(`[PoemsView] 📥 后台加载进度: ${progress}% (${currentLoadedCount}/${totalChunksNum} 分块, ${networkDataCount} 首诗词)`)
        }
      },
      onComplete: () => {
        const bgDuration = Math.round(performance.now() - bgStartTime)
        console.log(`[PoemsView] ✅ 后台加载完成: ${networkDataCount} 首诗词 - ${bgDuration}ms`)
        loadPoemsFromLoadedChunks()
        globalLoading.finish(bgTaskId)
      }
    })
  } catch (error) {
    globalLoading.update(initTaskId, { description: '加载失败，请刷新重试' })
    console.error('[PoemsView] ❌ 诗词数据加载失败:', error)
  } finally {
    const totalDuration = Math.round(performance.now() - totalStartTime)
    console.log(`[PoemsView] 🏁 总加载时间: ${totalDuration}ms`)
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
  const poem = poems.value.find(p => p.id === id)
  if (poem?.chunk_id !== undefined) {
    router.push({
      path: `/poems/${id}`,
      query: { chunk_id: poem.chunk_id.toString() }
    })
  } else {
    router.push(`/poems/${id}`)
  }
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
          label="总收录诗词"
          :value="`${globalTotal.toLocaleString()}`"
          :prefix-icon="LibraryOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="唐诗数量"
          :value="`${(poemCounts.tangshi || 0).toLocaleString()}`"
          :prefix-icon="FlameOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="宋诗数量"
          :value="`${(poemCounts.songshi || 0).toLocaleString()}`"
          :prefix-icon="SchoolOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="宋词数量"
          :value="`${(poemCounts.songci || 0).toLocaleString()}`"
          :prefix-icon="MusicalNotesOutline"
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
        { label: '已加载诗词', value: displayTotal.toLocaleString() + ' 首' },
        { label: '已加载唐诗', value: displayTangshi.toLocaleString() + ' 首' },
        { label: '已加载宋诗', value: displaySongshi.toLocaleString() + ' 首' },
        { label: '已加载宋词', value: displaySongci.toLocaleString() + ' 首' },
      ]"



      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
    />

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索标题或作者..."
      :total="totalCount"
      :query-time="searchStats.queryTime"
      :source="searchStats.source as any"
      :loading="isSearching"
      @search="handleSearch"
      @clear="clearFilters"
    >
      <template #filters>
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
      </template>
    </SearchContainer>

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
    padding: 12px;
  }

  .poems-grid {
    grid-template-columns: 1fr;
  }

  .filters-section {
    gap: 8px;
    padding: 12px;
  }

  .filters-section :deep(.n-space) {
    display: flex;
    flex-wrap: wrap;
    width: 100%;
    gap: 8px;
  }

  .filters-section :deep(.n-select),
  .filters-section :deep(.n-input) {
    flex: 1 1 calc(50% - 4px) !important;
    min-width: calc(50% - 4px) !important;
  }

  .filters-section :deep(.n-input) {
    flex: 1 1 100% !important;
    min-width: 100% !important;
  }

  .filters-section :deep(.n-button) {
    flex: 0 0 auto;
  }
}
</style>
