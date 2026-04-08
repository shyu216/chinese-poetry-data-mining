<!--
  文件: web/src/views/PoemsView.vue
  说明: 诗词列表页，支持按朝代/体裁筛选、搜索与按块（chunk）加载诗文摘要以支持大规模数据集的渐进加载。

  数据管线:
    - 元数据: 使用 `usePoems().loadMetadata()` 获取分片信息与统计。
    - 分片加载: `useChunkLoader` 按需加载诗文摘要分片并缓存在 IndexedDB 或内存中，`loadedPoems` 维护当前已加载条目。
    - 搜索: `usePoemSearch` 提供全文/倒排索引搜索，优先使用索引返回结果并补充分片数据。

  复杂度:
    - 渲染为 O(k)（k = 当前页或已加载条数）；分片加载为 O(t)，t = 已请求分片数；全量聚合/统计为 O(n)。
    - 空间: 客户端缓存分片会使空间逐渐增长到 O(n)，取决于已加载的分片数量。

  风险与优化建议:
    - 大量分片解析应避免在主线程执行，建议使用 Web Worker 或流式解析减少 UI 阻塞。
    - 渲染长列表应配合虚拟滚动以降低 DOM 压力。
    - 并发下载控制、后端分页与断点续传机制能提升稳定性。
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { usePoems, POEMS_SUMMARY_STORAGE } from '@/composables/usePoems'
import { useChunkLoader, CHUNK_LOADER_PREFERENCE_KEYS } from '@/composables/useChunkLoader'
import { getMetadata, getVerifiedChunkedCache } from '@/composables/useCache'
import { usePoemSearch } from '@/search'
import { useShuffle } from '@/composables/useShuffle'
import type { PoemSummary } from '@/composables/types'
import {
  NEmpty, NSelect,
  NButton, NGrid, NGridItem, NSpace, NTooltip
} from 'naive-ui'
import PoemList from '@/components/display/PoemList.vue'
import {
  BookOutline,
  ChevronForwardOutline,
  LibraryOutline, FlameOutline,
  SchoolOutline, MusicalNotesOutline,
  ShuffleOutline, RefreshOutline, DownloadOutline
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
  loadChunkSummaries,
  queryPoems
} = usePoems()

const chunkLoader = useChunkLoader({ preferenceKey: CHUNK_LOADER_PREFERENCE_KEYS.poems })

// 搜索模块
const { search: searchPoems, isReady: poemSearchReady } = usePoemSearch()
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: '' })

// 状态
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(24)
const loadedPoems = shallowRef<PoemSummary[]>([])
const hasMoreChunks = ref(true)
const isInitializing = ref(true)
const cachedChunksCount = ref(0)
const isLoadingMore = ref(false)

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

// 随机排序功能
const { isShuffled, shuffledItems: shuffledFilteredPoems, toggleShuffle, shuffle } = useShuffle({
  items: filteredPoems
})

// 显示逻辑：搜索模式显示搜索结果，否则显示过滤后的列表（支持随机排序）
const displayPoems = computed(() => {
  const query = searchQuery.value.trim()
  if (query && poemSearchReady.value) {
    return searchResults.value
  }
  return shuffledFilteredPoems.value
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
  if (count === 0) return '正在连接...'
  return `已加载 ${count.toLocaleString()} 首诗词`
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

  loading.startBlocking('诗词列表', '正在加载诗词数据...')
  isInitializing.value = true

  try {
    loading.updatePhase('metadata', '正在加载元数据...')
    console.log('[PoemsView] 📋 阶段1: 加载元数据...')
    const metaStartTime = performance.now()
    await loadMetadata()
    const totalChunksCount = totalChunks.value || 0
    console.log(`[PoemsView] ✅ 元数据加载完成: ${totalPoems.value} 首诗词, ${totalChunksCount} 个分块 - ${Math.round(performance.now() - metaStartTime)}ms`)

    loading.updateProgress(1, 3, '正在加载首批数据...')
    console.log('[PoemsView] ⚡ 阶段2: 快速加载首批数据...')
    const quickStartTime = performance.now()
    const firstChunkIds = await loadCachedChunks(true)
    console.log(`[PoemsView] ✅ 首批数据加载完成 - ${Math.round(performance.now() - quickStartTime)}ms`)

    loading.updateProgress(2, 3, '准备就绪...')
    loading.updatePhase('complete', '数据加载完成')
    loading.updateProgress(3, 3)
    setTimeout(() => loading.finish(), 200)
    isInitializing.value = false

    console.log('[PoemsView] 🎨 界面已可交互，开始后台加载剩余数据...')

    const remainingStartTime = performance.now()
    if (chunkLoader.autoLoadEnabled.value) {
      loading.startNonBlocking('补充诗词数据', '正在加载剩余数据...')
    } else {
      console.log('[PoemsView] autoLoadOnEnter=false — skip unified non-blocking toast until user resumes chunk load')
    }

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
          loadedPoems.value = [...loadedPoems.value, ...chunkData]
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

      const runNetworkChunkLoad = () =>
        chunkLoader.loadChunks<PoemSummary[]>(unloadedChunkIds, loadChunkSummaries, {
          concurrency: 5,
          chunkDelay: 0,
          onChunkLoaded: (chunkId, poems) => {
            const poemsArray = poems as PoemSummary[]
            loadedPoems.value = [...loadedPoems.value, ...poemsArray]
            networkDataCount += poemsArray.length

            loadedCount++
            const progress = Math.round((loadedCount / totalChunksCount) * 100)

            if (loadedCount % Math.max(1, Math.floor(totalChunksCount / 10)) === 0) {
              const phases = ['正在读取诗词数据...', '正在整理诗词分类...', '正在加载诗词信息...', '正在构建诗词列表...']
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

      if (chunkLoader.autoLoadEnabled.value) {
        await runNetworkChunkLoad()
      } else {
        console.log(
          '[PoemsView] autoLoadOnEnter=false (localStorage) — network chunk load started paused; not awaiting loadData'
        )
        void runNetworkChunkLoad()
      }
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

// 监听过滤器变化
watch([dynastyFilter, genreFilter], () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="poems-view">
    <PageHeader
      title="诗词列表 "
      :subtitle="`共收录 ${dynamicStats.total.toLocaleString()} 首诗词，支持朝代、体裁筛选`"
      :icon="BookOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
        <NGridItem>
          <StatsCard
            label="诗词总数"
            :value="dynamicStats.total.toLocaleString()"
            :prefix-icon="LibraryOutline"
          />
        </NGridItem>
        <NGridItem>
          <StatsCard
            label="唐诗"
            :value="dynamicStats.tangshi.toLocaleString()"
            :prefix-icon="FlameOutline"
          />
        </NGridItem>
        <NGridItem>
          <StatsCard
            label="宋诗"
            :value="dynamicStats.songshi.toLocaleString()"
            :prefix-icon="SchoolOutline"
          />
        </NGridItem>
        <NGridItem>
          <StatsCard
            label="宋词"
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
        { label: '唐诗', value: dynamicStats.tangshi.toLocaleString() + ' 首' },
        { label: '宋诗', value: dynamicStats.songshi.toLocaleString() + ' 首' },
        { label: '宋词', value: dynamicStats.songci.toLocaleString() + ' 首' },
      ]"
      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
    />

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索诗词或作者..."
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
        <NSpace>
          <NTooltip trigger="hover">
            <template #trigger>
              <NButton
                :type="isShuffled ? 'primary' : 'default'"
                :ghost="!isShuffled"
                size="medium"
                @click="toggleShuffle"
                :disabled="searchQuery.trim().length > 0"
              >
                <template #icon>
                  <ShuffleOutline />
                </template>
                {{ isShuffled ? '已随机' : '随机排序' }}
              </NButton>
            </template>
            {{ isShuffled ? '点击恢复默认排序' : '点击随机打乱诗词顺序' }}
          </NTooltip>
          <NTooltip v-if="isShuffled" trigger="hover">
            <template #trigger>
              <NButton
                size="medium"
                @click="shuffle"
              >
                <template #icon>
                  <RefreshOutline />
                </template>
                换一批
              </NButton>
            </template>
            重新随机排序
          </NTooltip>
        </NSpace>
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
      </template>
    </NEmpty>

    <div v-else-if="displayPoems.length > 0" class="poems-container">
      <PoemList
        :poems="displayPoems"
        :total="searchQuery.trim() ? searchTotal : undefined"
        v-model:page="currentPage"
        v-model:page-size="pageSize"
        :show-pagination="true"
        :grid-view="true"
        @view-poem="goToPoemDetail"
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

@media (max-width: 768px) {
  .poems-view {
    padding: 16px;
  }

  .poems-grid {
    grid-template-columns: 1fr;
  }
}
</style>
