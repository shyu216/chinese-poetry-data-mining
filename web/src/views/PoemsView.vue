<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePoemsV2, POEMS_SUMMARY_STORAGE } from '@/composables/usePoemsV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { getMetadata, getVerifiedChunkedCache } from '@/composables/useCacheV2'
import { usePoemSearch } from '@/search'
import type { PoemSummary } from '@/composables/types'
import {
  NEmpty, NSelect,
  NButton, NPagination, NGrid, NGridItem
} from 'naive-ui'
import {
  BookOutline,
  ChevronForwardOutline,
  LibraryOutline, FlameOutline,
  SchoolOutline, MusicalNotesOutline
} from '@vicons/ionicons5'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatsCard from '@/components/display/StatsCard.vue'
import DynastyBadge from '@/components/ui/badge/DynastyBadge.vue'
import ChunkLoaderStatus from '@/components/feedback/ChunkLoaderStatus.vue'
import { SearchContainer } from '@/components/search'
import { useLoading } from '@/composables/useLoading'

const router = useRouter()
const loading = useLoading()
const {
  metadata,
  totalPoems,
  totalChunks,
  dynasties,
  genres,
  poemCounts,
  loadMetadata,
  loadChunkSummaries
} = usePoemsV2()

const chunkLoader = useChunkLoader()

// 搜索模块
const { search: searchPoems, isReady: poemSearchReady } = usePoemSearch()
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: '' })

// 状态
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(24)
const loadedPoems = ref<PoemSummary[]>([])
const hasMoreChunks = ref(true)
const isInitializing = ref(true)
const cachedChunksCount = ref(0)

// 过滤器
const dynastyFilter = ref<string | null>(null)
const genreFilter = ref<string | null>(null)

// 统计数据
const dynamicStats = computed(() => {
  const list = loadedPoems.value
  const total = list.length
  const tangshi = list.filter(p => p.dynasty === '唐' && p.genre === '诗').length
  const songshi = list.filter(p => p.dynasty === '宋' && p.genre === '诗').length
  const songci = list.filter(p => p.dynasty === '宋' && p.genre === '词').length

  return { total, tangshi, songshi, songci }
})

// 过滤器选项
const dynastyOptions = computed(() => [
  { label: '全部朝代', value: '' },
  ...dynasties.value.map(d => ({ label: d, value: d }))
])

const genreOptions = computed(() => [
  { label: '全部体裁', value: '' },
  ...genres.value.map(g => ({ label: g, value: g }))
])

// 搜索相关
const searchResults = ref<PoemSummary[]>([])
const searchTotal = ref(0)

const performSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query || !poemSearchReady.value) {
    searchResults.value = []
    searchTotal.value = 0
    return
  }

  isSearching.value = true
  try {
    const result = await searchPoems(query, {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
      filters: {
        dynasty: dynastyFilter.value || undefined,
        genre: genreFilter.value || undefined
      }
    })
    searchResults.value = result.items
    searchTotal.value = result.total
    searchStats.value = { queryTime: result.queryTime, source: result.source }
  } finally {
    isSearching.value = false
  }
}

// 列表过滤（非搜索模式下）
const filteredPoems = computed(() => {
  let result = loadedPoems.value

  if (dynastyFilter.value) {
    result = result.filter(p => p.dynasty === dynastyFilter.value)
  }
  if (genreFilter.value) {
    result = result.filter(p => p.genre === genreFilter.value)
  }

  return result
})

// 显示逻辑：搜索模式显示搜索结果，否则显示过滤后的列表
const displayPoems = computed(() => {
  const query = searchQuery.value.trim()
  if (query && poemSearchReady.value) {
    return searchResults.value
  }
  return filteredPoems.value
})

const displayTotal = computed(() => {
  const query = searchQuery.value.trim()
  if (query && poemSearchReady.value) {
    return searchTotal.value
  }
  return filteredPoems.value.length
})

const totalPages = computed(() => {
  return Math.ceil(displayTotal.value / pageSize.value)
})

const paginatedPoems = computed(() => {
  // 搜索模式下，搜索结果已经分页
  const query = searchQuery.value.trim()
  if (query && poemSearchReady.value) {
    return displayPoems.value
  }
  // 列表模式下，内存分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return displayPoems.value.slice(start, end)
})

// 加载提示
const loadingHint = computed(() => {
  const count = loadedPoems.value.length
  if (count === 0) return '🚀 正在连接...'
  return `📚 已加载 ${count.toLocaleString()} 首诗词...`
})

// 从缓存加载
const loadCachedChunks = async (quickMode = false): Promise<number[]> => {
  console.log(`[PoemsView] 🔄 开始加载本地缓存${quickMode ? ' (快速模式)' : ''}...`)
  const startTime = performance.now()

  const meta = await getMetadata(POEMS_SUMMARY_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  console.log(`[PoemsView] 📦 发现 ${loadedChunkIds.length} 个缓存分块`)

  if (loadedChunkIds.length === 0) {
    console.log('[PoemsView] ⚠️ 无缓存数据，将从服务器加载')
    return []
  }

  // 快速模式：只读取第一个分块
  if (quickMode) {
    const firstChunkId = loadedChunkIds[0]!
    console.log(`[PoemsView] ⚡ 快速模式：优先加载分块 #${firstChunkId}`)

    const chunkData = await getVerifiedChunkedCache<PoemSummary[]>(POEMS_SUMMARY_STORAGE, firstChunkId)

    if (chunkData && Array.isArray(chunkData) && chunkData.length > 0) {
      loadedPoems.value = chunkData
      cachedChunksCount.value = 1
      console.log(`[PoemsView] ✅ 快速加载完成: ${chunkData.length} 首诗词 - ${Math.round(performance.now() - startTime)}ms`)
    }

    return [firstChunkId]
  }

  // 完整模式：读取所有缓存分块
  cachedChunksCount.value = loadedChunkIds.length
  const cachedPoems: PoemSummary[] = []
  console.log(`[PoemsView] 📖 开始读取 ${loadedChunkIds.length} 个缓存分块...`)

  for (const chunkId of loadedChunkIds) {
    const chunkStartTime = performance.now()
    const chunkData = await getVerifiedChunkedCache<PoemSummary[]>(POEMS_SUMMARY_STORAGE, chunkId)
    const chunkDuration = Math.round(performance.now() - chunkStartTime)

    if (chunkData && Array.isArray(chunkData)) {
      cachedPoems.push(...chunkData)
      console.log(`[PoemsView]   ├─ 分块 #${chunkId}: ${chunkData.length} 首诗词 (${chunkDuration}ms)`)
    }
  }

  if (cachedPoems.length > 0) {
    loadedPoems.value = cachedPoems
  }

  const totalDuration = Math.round(performance.now() - startTime)
  console.log(`[PoemsView] ✅ 缓存加载完成: ${cachedPoems.length} 首诗词 - ${totalDuration}ms`)

  return loadedChunkIds
}

// 主加载函数
const loadData = async () => {
  console.log('[PoemsView] 🚀 开始加载数据...')
  const totalStartTime = performance.now()

  loading.startBlocking('翰墨集珍', '正在开启诗词宝库...')
  isInitializing.value = true

  try {
    // 阶段1: 加载元数据
    loading.updatePhase('metadata', '正在读取诗词索引...')
    console.log('[PoemsView] 📋 阶段1: 加载元数据...')
    const metaStartTime = performance.now()
    await loadMetadata()
    const totalChunksCount = totalChunks.value || 0
    console.log(`[PoemsView] ✅ 元数据加载完成: ${totalPoems.value} 首诗词, ${totalChunksCount} 个分块 - ${Math.round(performance.now() - metaStartTime)}ms`)

    // 阶段2: 快速加载第一个缓存分块
    loading.updateProgress(1, 3, '正在加载首批诗词...')
    console.log('[PoemsView] ⚡ 阶段2: 快速加载首批数据...')
    const quickStartTime = performance.now()
    const firstChunkIds = await loadCachedChunks(true)
    console.log(`[PoemsView] ✅ 首批数据加载完成 - ${Math.round(performance.now() - quickStartTime)}ms`)

    // 阶段3: 立即解除阻塞，展示界面
    loading.updateProgress(2, 3, '准备就绪...')
    loading.updatePhase('complete', '诗词宝库已开，请君品鉴')
    loading.updateProgress(3, 3)
    setTimeout(() => loading.finish(), 200)
    isInitializing.value = false

    console.log('[PoemsView] 🎨 界面已可交互，开始后台加载剩余数据...')

    // 阶段4: 后台加载剩余数据
    const remainingStartTime = performance.now()
    loading.startNonBlocking('补充诗词数据', '正在汇聚千年文脉...')

    // 加载剩余缓存分块
    const meta = await getMetadata(POEMS_SUMMARY_STORAGE)
    const allCachedChunkIds = meta?.loadedChunkIds || []
    const remainingCachedIds = allCachedChunkIds.filter(id => !firstChunkIds.includes(id))

    if (remainingCachedIds.length > 0) {
      console.log(`[PoemsView] 💾 后台加载剩余 ${remainingCachedIds.length} 个缓存分块...`)
      let loadedCachedCount = 0
      for (const chunkId of remainingCachedIds) {
        const chunkData = await getVerifiedChunkedCache<PoemSummary[]>(POEMS_SUMMARY_STORAGE, chunkId)
        if (chunkData && Array.isArray(chunkData)) {
          loadedPoems.value.push(...chunkData)
          cachedChunksCount.value++
          loadedCachedCount++
          // 每3个分块输出一次日志
          if (loadedCachedCount % 3 === 0) {
            console.log(`[PoemsView] 📥 缓存加载进度: ${loadedCachedCount}/${remainingCachedIds.length} 分块`)
          }
        }
      }
      console.log(`[PoemsView] ✅ 剩余缓存加载完成，当前共 ${loadedPoems.value.length} 首诗词`)
    }

    // 加载网络分块
    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !allCachedChunkIds.includes(id))

    if (unloadedChunkIds.length === 0) {
      console.log('[PoemsView] ✨ 所有数据已加载完成')
      hasMoreChunks.value = false
      loading.finish()
    } else {
      console.log(`[PoemsView] 🌐 开始加载 ${unloadedChunkIds.length} 个网络分块...`)
      let loadedCount = allCachedChunkIds.length
      let networkDataCount = 0

      await chunkLoader.loadChunks<PoemSummary[]>(unloadedChunkIds, loadChunkSummaries, {
        concurrency: 5,
        chunkDelay: 0,
        onChunkLoaded: (chunkId, poems) => {
          const poemsArray = poems as PoemSummary[]
          loadedPoems.value.push(...poemsArray)
          networkDataCount += poemsArray.length

          loadedCount++
          const progress = Math.round((loadedCount / totalChunksCount) * 100)

          if (loadedCount % Math.max(1, Math.floor(totalChunksCount / 10)) === 0) {
            const phases = ['正在读取诗作档案...', '正在整理诗词分类...', '正在汇聚千年文脉...', '正在构建诗词图谱...']
            const phase = phases[Math.floor((loadedCount / totalChunksCount) * phases.length)] || phases[0]
            loading.updateProgress(loadedCount, totalChunksCount, `${phase} (${loadedCount}/${totalChunksCount})`)
            console.log(`[PoemsView] 📥 后台加载进度: ${progress}% (${loadedCount}/${totalChunksCount} 分块, +${networkDataCount} 首诗词)`)
          }
        },
        onComplete: () => {
          const bgDuration = Math.round(performance.now() - remainingStartTime)
          console.log(`[PoemsView] ✅ 后台加载完成: 共 ${loadedPoems.value.length} 首诗词 - ${bgDuration}ms`)
          hasMoreChunks.value = false
          loading.finish()
        }
      })
    }
  } catch (error) {
    loading.error('加载失败，请刷新重试')
    console.error('[PoemsView] ❌ 诗词数据加载失败:', error)
    isInitializing.value = false
  } finally {
    const totalDuration = Math.round(performance.now() - totalStartTime)
    console.log(`[PoemsView] 🏁 总加载时间: ${totalDuration}ms`)
  }
}

// 导航
const goToPoemDetail = (poem: PoemSummary) => {
  if (poem.chunk_id !== undefined) {
    router.push({
      path: `/poems/${poem.id}`,
      query: { chunk_id: poem.chunk_id.toString() }
    })
  } else {
    router.push(`/poems/${poem.id}`)
  }
}

// 清除过滤器
const clearFilters = () => {
  dynastyFilter.value = null
  genreFilter.value = null
  searchQuery.value = ''
  currentPage.value = 1
}

// 生命周期
onMounted(() => {
  loadData()
})

// 监听搜索词变化
watch(searchQuery, () => {
  currentPage.value = 1
  performSearch()
})
</script>

<template>
  <div class="poems-view">
    <PageHeader
      title="翰墨集珍"
      :subtitle="`收录 ${totalPoems.toLocaleString()} 首诗词，按朝代、体裁筛选`"
      :icon="BookOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard
          label="总收录诗词"
          :value="dynamicStats.total.toLocaleString()"
          :prefix-icon="LibraryOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="唐诗数量"
          :value="dynamicStats.tangshi.toLocaleString()"
          :prefix-icon="FlameOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="宋诗数量"
          :value="dynamicStats.songshi.toLocaleString()"
          :prefix-icon="SchoolOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="宋词数量"
          :value="dynamicStats.songci.toLocaleString()"
          :prefix-icon="MusicalNotesOutline"
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
      title="加载诗词数据"
      :hint="loadingHint"
      :stats="[
        { label: '已加载诗词', value: dynamicStats.total.toLocaleString() + ' 首' },
        { label: '当前唐诗', value: dynamicStats.tangshi.toLocaleString() + ' 首' },
        { label: '当前宋诗', value: dynamicStats.songshi.toLocaleString() + ' 首' },
        { label: '当前宋词', value: dynamicStats.songci.toLocaleString() + ' 首' },
      ]"
      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
    />

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索诗词、作者..."
      :total="displayTotal"
      :query-time="searchStats.queryTime"
      :source="searchStats.source as any"
      :loading="isSearching"
      @search="performSearch"
      @clear="clearFilters"
    >
      <template #filters>
        <NSelect
          v-model:value="dynastyFilter"
          :options="dynastyOptions"
          placeholder="选择朝代"
          style="width: 130px"
          size="medium"
          clearable
        />
        <NSelect
          v-model:value="genreFilter"
          :options="genreOptions"
          placeholder="选择体裁"
          style="width: 130px"
          size="medium"
          clearable
        />
      </template>
    </SearchContainer>

    <!-- 加载中状态 -->
    <NEmpty
      v-if="isInitializing || (loadedPoems.length === 0 && hasMoreChunks && !searchQuery.trim() && !dynastyFilter && !genreFilter)"
      description="正在加载诗词数据..."
    />

    <!-- 无搜索结果状态 -->
    <NEmpty
      v-else-if="displayPoems.length === 0"
      :description="hasMoreChunks ? '加载更多数据可能会有结果' : '暂无诗词数据'"
    >
      <template #extra>
        <NButton v-if="hasMoreChunks" @click="clearFilters">
          清除筛选
        </NButton>
        <NButton v-else @click="clearFilters">
          清除筛选
        </NButton>
      </template>
    </NEmpty>

    <div v-else-if="displayPoems.length > 0" class="poems-container">
      <div class="poems-grid">
        <article
          v-for="poem in paginatedPoems"
          :key="poem.id"
          class="poem-card"
          @click="goToPoemDetail(poem)"
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
    </div>

    <div class="pagination-wrapper" v-if="totalPages > 1">
      <NPagination
        v-model:page="currentPage"
        :page-count="totalPages"
        :page-size="pageSize"
        show-size-picker
        :page-sizes="[12, 24, 48, 96]"
        @update:page-size="pageSize = $event"
      />
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

.divider {
  color: var(--color-border, #d9d9d9);
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
}
</style>
