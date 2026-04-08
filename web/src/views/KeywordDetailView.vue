<!--
  文件: web/src/views/KeywordDetailView.vue
  说明: 关键词详情页，展示某关键词下的诗词列表、统计（朝代/体裁分布）与可视化（Plotly），并支持批量分片加载诗词内容以提升性能。

  数据管线:
    - 索引检索: 通过 `useKeywordIndex` / `useSearchIndex` 获取匹配诗词 id 列表。
    - 批量加载: 使用分批策略（`loadPoemsBatch`，batchSize = 50）先从索引获取摘要（包含 chunk_id），再按 chunk 批量加载详情并合并到页面列表。
    - 可视化: 统计结果计算后使用 Plotly 绘图（`newPlot` / `react` / `purge`）。

  复杂度:
    - 索引查询与分页为 O(k)，k = 返回条数；批量分片加载总成本为 O(n)，但通过分批减少单次峰值压力。
    - 可视化库（Plotly）在数据量大时会占用较多内存并降低交互性能。

  注意与建议:
    - 批量加载采用分批策略以避免一次性请求过多，但仍需限流与并发控制（网络与 IndexedDB 写入）。
    - Plotly 渲染复杂图表时建议对数据进行降采样或使用轻量级图表库以提升性能。
    - 建议在长时间或大数据加载时展示进度并支持取消操作；重试与错误回退策略也很重要。
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useKeywordIndex } from '@/composables/useKeywordIndex'
import { usePoems } from '@/composables/usePoems'
import { useSearchIndex } from '@/composables/useSearchIndex'
import { useWordcount } from '@/composables/useWordcount'
import type { PoemSummary } from '@/composables/types'
import {
  NCard, NSpin, NEmpty, NTag, NButton, NSpace,
  NPageHeader, NGrid, NGridItem, NBackTop, NPagination
} from 'naive-ui'
import { StatsCard } from '@/components/display'
import PoemList from '@/components/display/PoemList.vue'
import WordCloud from '@/components/display/WordCloud.vue'
import useFasttextOnnx from '@/composables/useFasttextOnnx'
import {
  ArrowBackOutline, SearchOutline, BookOutline,
  TextOutline, TrendingUpOutline, ListOutline
} from '@vicons/ionicons5'
import { useLoading } from '@/composables/useLoading'
import * as Plotly from 'plotly.js-dist-min'
// 为 Plotly 添加类型声明
declare module 'plotly.js-dist-min' {
  export interface PlotlyHTMLElement extends HTMLElement { }
  export interface PlotlyConfig {
    responsive?: boolean
    displayModeBar?: boolean
  }
  export function newPlot(
    element: HTMLElement | string,
    data: any[],
    layout?: any,
    config?: PlotlyConfig
  ): any
  export function react(
    element: HTMLElement | string,
    data: any[],
    layout?: any,
    config?: PlotlyConfig
  ): any
  export function purge(element: HTMLElement | string): void
}

const route = useRoute()
const router = useRouter()
const loading = useLoading()
const keywordIndex = useKeywordIndex()
const poems = usePoems()
const searchIndex = useSearchIndex()
const wordcount = useWordcount()

const keyword = computed(() => route.params.word as string)
const poemIds = ref<string[]>([])
const poemsList = ref<PoemSummary[]>([])
const isLoading = ref(true)
const wordRank = ref<number | null>(null)
const wordCount = ref<number | null>(null)

// 分页相关
const page = ref(1)
const pageSize = ref(24)
const loadingPoems = ref(false)

const totalPoems = computed(() => poems.totalPoems.value)

const dynastyStats = computed(() => {
  const targetPoems = allPoems.value.length > 0 ? allPoems.value : poemsList.value
  const stats: Record<string, number> = {}
  targetPoems.forEach(p => {
    const d = p.dynasty || '未知'
    stats[d] = (stats[d] || 0) + 1
  })
  return Object.entries(stats)
    .map(([dynasty, count]) => ({ dynasty, count }))
    .sort((a, b) => b.count - a.count)
})

const genreStats = computed(() => {
  const targetPoems = allPoems.value.length > 0 ? allPoems.value : poemsList.value
  const stats: Record<string, number> = {}
  targetPoems.forEach(p => {
    const g = p.genre || '未知'
    stats[g] = (stats[g] || 0) + 1
  })
  return Object.entries(stats)
    .map(([genre, count]) => ({ genre, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

// 批量加载诗词（带分页）- 使用 chunk_id 优化
const loadPoemsBatch = async (ids: string[], updateUI = false): Promise<PoemSummary[]> => {
  console.log(`[KeywordDetail] loadPoemsBatch START: ${ids.length} poems, updateUI=${updateUI}`)
  const batchStartTime = Date.now()
  const batchSize = 50 // 每批加载50首

  // 统计信息
  let totalChunksLoaded = 0
  let totalFromCache = 0
  const uniqueChunks = new Set<number>()
  const results: PoemSummary[] = []

  for (let i = 0; i < ids.length; i += batchSize) {
    const batch = ids.slice(i, i + batchSize)
    console.log(`[KeywordDetail] Batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(ids.length / batchSize)}: loading ${batch.length} poems`)

    // 1. 先从 poem_index 获取诗词数据（包含 chunk_id）
    const step1Start = Date.now()
    const poemSummaries = await searchIndex.getPoemSummariesByIds(batch)
    console.log(`[KeywordDetail]   -> Got ${poemSummaries.size} summaries from index in ${Date.now() - step1Start}ms`)

    // 2. 提取 chunk_ids 用于批量加载详情
    const idsWithChunkIds: string[] = []
    const chunkIds: number[] = []

    for (const [id, summary] of poemSummaries.entries()) {
      if (summary.chunk_id !== undefined) {
        idsWithChunkIds.push(id)
        chunkIds.push(summary.chunk_id)
      }
    }
    console.log(`[KeywordDetail]   -> ${idsWithChunkIds.length}/${batch.length} poems have chunk_id`)

    // 3. 使用 chunk_id 批量加载诗词详情
    let batchResults: (import('@/composables/types').PoemDetail | null)[] = []
    const step3Start = Date.now()

    // 统计chunk使用情况
    chunkIds.forEach(c => uniqueChunks.add(c))

    if (idsWithChunkIds.length === batch.length) {
      // 所有诗词都有 chunk_id，使用优化批量加载
      console.log(`[KeywordDetail]   -> Using optimized batch loading with ${chunkIds.length} chunks (unique: ${new Set(chunkIds).size})`)
      const poemsWithDetails = await poems.getPoemsByIds(idsWithChunkIds, chunkIds)
      // 保持原始顺序
      batchResults = batch.map(id => poemsWithDetails.find(p => p.id === id) || null)
    } else {
      // 部分诗词没有 chunk_id，回退到逐个加载
      console.warn(`[KeywordDetail] Some poems missing chunk_id (${idsWithChunkIds.length}/${batch.length}), falling back to individual loading`)
      batchResults = await Promise.all(batch.map(id => poems.getPoemById(id)))
    }
    const loadedCount = batchResults.filter(p => p !== null).length
    console.log(`[KeywordDetail]   -> Loaded ${loadedCount}/${batch.length} poems in ${Date.now() - step3Start}ms`)

    for (const poem of batchResults) {
      if (poem) {
        results.push({
          id: poem.id,
          title: poem.title,
          author: poem.author,
          dynasty: poem.dynasty,
          genre: poem.genre,
          chunk_id: poemSummaries.get(poem.id)?.chunk_id
        })
      }
    }

    // 只在初始加载时更新UI，避免后台加载时覆盖当前页
    if (updateUI && i === 0 && results.length > 0) {
      console.log(`[KeywordDetail] Updating UI with first ${results.length} poems`)
      poemsList.value = results.slice(0, pageSize.value)
    }
  }

  const duration = Date.now() - batchStartTime
  const poemsPerSecond = Math.round(results.length / (duration / 1000))
  console.log(`[KeywordDetail] loadPoemsBatch DONE: ${results.length} poems in ${duration}ms (${poemsPerSecond} poems/s, ${uniqueChunks.size} unique chunks)`)
  return results
}

let isLoadingData = false

const loadData = async () => {
  // 防止重复加载
  if (isLoadingData) {
    console.log(`[KeywordDetail] loadData SKIP: already loading for "${keyword.value}"`)
    return
  }
  isLoadingData = true

  console.log(`[KeywordDetail] loadData START for keyword: "${keyword.value}"`)
  const startTime = Date.now()
  const memoryBefore = (performance as any).memory?.usedJSHeapSize / 1024 / 1024 || 0
  console.log(`[KeywordDetail] Memory before: ${memoryBefore.toFixed(2)}MB`)

  // 步骤 1: 初始化 - 开始 blocking loading
  loading.startBlocking('关键词详情', `查询"${keyword.value}"...`)
  isLoading.value = true
  loadingPoems.value = true
  poemsList.value = []
  page.value = 1

  try {
    // 步骤 2: 检索相关诗词（必须完成，因为需要知道总数）
    loading.updatePhase('search', '检索相关诗词...')
    loading.updateProgress(0, 2)
    console.log(`[KeywordDetail] Step 1: Getting keyword poem IDs...`)
    const step1Start = Date.now()
    poemIds.value = await keywordIndex.getKeywordPoemIds(keyword.value)
    console.log(`[KeywordDetail] Step 1 DONE: Found ${poemIds.value.length} poems in ${Date.now() - step1Start}ms`)

    if (poemIds.value.length === 0) {
      console.log(`[KeywordDetail] No poems found, returning early`)
      loading.updatePhase('complete', '未找到相关诗词')
      loading.finish()
      isLoading.value = false
      loadingPoems.value = false
      return
    }

    // 步骤 3: 快速加载第一页诗词（渐进式加载核心）
    loading.updateProgress(1, 2, `正在加载首批 ${Math.min(pageSize.value, poemIds.value.length)} 首诗词...`)
    const firstPageIds = poemIds.value.slice(0, pageSize.value)
    console.log(`[KeywordDetail] Step 2: Loading first page with ${firstPageIds.length} poems...`)

    const step2Start = Date.now()
    const firstPageResults = await loadPoemsBatch(firstPageIds, true)
    console.log(`[KeywordDetail] Step 2 DONE: Loaded ${firstPageResults.length} poems in ${Date.now() - step2Start}ms`)

    poemsList.value = firstPageResults

    // 步骤 4: 立即解除阻塞，展示界面！
    loading.updateProgress(2, 2, '准备就绪...')
    loading.updatePhase('complete', '数据已就绪')
    setTimeout(() => loading.finish(), 200)
    isLoading.value = false
    console.log(`[KeywordDetail] 🎉 界面已可交互，开始后台加载剩余数据...`)

    // 步骤 5: 后台加载剩余诗词 + 统计数据
    if (poemIds.value.length > pageSize.value) {
      const remainingIds = poemIds.value.slice(pageSize.value)
      console.log(`[KeywordDetail] Step 3: Loading remaining ${remainingIds.length} poems in background...`)
      loading.startNonBlocking('补充诗词数据', `正在加载剩余 ${remainingIds.length} 首诗词...`)
      loadRemainingPoems(remainingIds)
    } else {
      console.log(`[KeywordDetail] No remaining poems to load`)
      loadingPoems.value = false
      // 直接使用当前数据作为完整数据
      allPoems.value = poemsList.value
    }

    // 后台获取分词数据
    wordcount.getTopWords(10000).then(allWords => {
      const foundWord = allWords.find(w => w.word === keyword.value)
      if (foundWord) {
        wordRank.value = foundWord.rank
        wordCount.value = foundWord.count
      }
    })
    // 同步加载相似词（非阻塞）
    loadSimilarWords().catch(e => console.warn('[KeywordDetail] loadSimilarWords failed', e))
  } catch (e) {
    console.error('[KeywordDetail] ERROR in loadData:', e)
    loading.error('加载失败')
    isLoading.value = false
  } finally {
    const memoryAfter = (performance as any).memory?.usedJSHeapSize / 1024 / 1024 || 0
    console.log(`[KeywordDetail] Memory after: ${memoryAfter.toFixed(2)}MB (delta: ${(memoryAfter - memoryBefore).toFixed(2)}MB)`)
    console.log(`[KeywordDetail] loadData FINALLY, total time: ${Date.now() - startTime}ms`)
    isLoadingData = false
  }
}

// 后台加载剩余诗词
const allPoems = ref<PoemSummary[]>([])
let isLoadingRemaining = false

const loadRemainingPoems = async (ids: string[]) => {
  // 防止重复后台加载
  if (isLoadingRemaining) {
    console.log(`[KeywordDetail] loadRemainingPoems SKIP: already loading`)
    return
  }
  isLoadingRemaining = true

  console.log(`[KeywordDetail] loadRemainingPoems START: ${ids.length} poems`)
  const startTime = Date.now()
  const memoryBefore = (performance as any).memory?.usedJSHeapSize / 1024 / 1024 || 0

  try {
    // 后台加载，不更新UI，避免覆盖当前页
    const remaining = await loadPoemsBatch(ids, false)
    allPoems.value = [...poemsList.value, ...remaining]
    loadingPoems.value = false
    loading.finish()

    const memoryAfter = (performance as any).memory?.usedJSHeapSize / 1024 / 1024 || 0
    console.log(`[KeywordDetail] loadRemainingPoems DONE: ${allPoems.value.length} total poems in ${Date.now() - startTime}ms`)
    console.log(`[KeywordDetail] Memory delta: ${(memoryAfter - memoryBefore).toFixed(2)}MB`)

    // 数据加载完成后更新图表
    setTimeout(() => {
      renderCharts()
    }, 100)
  } catch (e) {
    console.error('[KeywordDetail] ERROR in loadRemainingPoems:', e)
    loadingPoems.value = false
    loading.finish()
  } finally {
    isLoadingRemaining = false
  }
}

// 图表相关
const dynastyChartRef = ref<HTMLDivElement | null>(null)
const genreChartRef = ref<HTMLDivElement | null>(null)
const dynastyChartInstance = ref<any>(null)
const genreChartInstance = ref<any>(null)

const renderCharts = () => {
  // 渲染朝代分布图表
  if (dynastyChartRef.value) {
    const targetPoems = allPoems.value.length > 0 ? allPoems.value : poemsList.value
    const dynastyData = dynastyStats.value

    if (dynastyData.length > 0) {
      const labels = dynastyData.map(d => d.dynasty)
      const values = dynastyData.map(d => d.count)
      const colors = dynastyData.map(d => getDynastyColor(d.dynasty))

      const data = [{
        type: 'pie',
        values: values,
        labels: labels,
        hole: 0.4,
        marker: {
          colors: colors
        },
        textinfo: 'label+percent',
        textposition: 'outside',
        hoverinfo: 'label+value+percent'
      }]

      const layout = {
        title: {
          text: '朝代分布',
          font: {
            size: 16,
            weight: 'bold'
          }
        },
        showlegend: true,
        legend: {
          position: 'right'
        },
        margin: {
          l: 20,
          r: 80,
          t: 40,
          b: 20
        }
      }

      if (dynastyChartInstance.value) {
        Plotly.react(dynastyChartRef.value, data, layout)
      } else {
        dynastyChartInstance.value = Plotly.newPlot(dynastyChartRef.value, data, layout, {
          responsive: true,
          displayModeBar: false
        })
      }
    }
  }

  // 渲染体裁分布图表
  if (genreChartRef.value) {
    const targetPoems = allPoems.value.length > 0 ? allPoems.value : poemsList.value
    const genreData = genreStats.value

    if (genreData.length > 0) {
      const labels = genreData.map(g => g.genre)
      const values = genreData.map(g => g.count)
      const colors = [
        '#8b2635', '#1e40af', '#047857', '#b45309', '#7c3aed',
        '#dc2626', '#0369a1', '#16a34a', '#9333ea', '#0284c7'
      ]

      const data = [{
        type: 'pie',
        values: values,
        labels: labels,
        hole: 0.4,
        marker: {
          colors: colors
        },
        textinfo: 'label+percent',
        textposition: 'outside',
        hoverinfo: 'label+value+percent'
      }]

      const layout = {
        title: {
          text: '体裁分布',
          font: {
            size: 16,
            weight: 'bold'
          }
        },
        showlegend: true,
        legend: {
          position: 'right'
        },
        margin: {
          l: 20,
          r: 80,
          t: 40,
          b: 20
        }
      }

      if (genreChartInstance.value) {
        Plotly.react(genreChartRef.value, data, layout)
      } else {
        genreChartInstance.value = Plotly.newPlot(genreChartRef.value, data, layout, {
          responsive: true,
          displayModeBar: false
        })
      }
    }
  }
}

onMounted(() => {
  loadData()
})

watch(keyword, () => {
  loadData()
})

// 监听数据变化，更新图表
watch([dynastyStats, genreStats, allPoems], () => {
  setTimeout(() => {
    renderCharts()
  }, 100)
}, { deep: true })

onUnmounted(() => {
  // 清理图表实例
  if (dynastyChartInstance.value) {
    Plotly.purge(dynastyChartRef.value!)
  }
  if (genreChartInstance.value) {
    Plotly.purge(genreChartRef.value!)
  }
})

// 处理分页变化
const handlePageChange = async (newPage: number) => {
  page.value = newPage
  const start = (newPage - 1) * pageSize.value
  const end = start + pageSize.value

  // 如果已经加载了所有诗词，直接从缓存取
  if (allPoems.value.length >= poemIds.value.length) {
    poemsList.value = allPoems.value.slice(start, end)
    return
  }

  // 否则按需加载 - 使用 chunk_id 优化
  const pageIds = poemIds.value.slice(start, end)
  const pageResults = await loadPoemsBatch(pageIds, true)

  poemsList.value = pageResults
}

const handlePageSizeChange = (newSize: number) => {
  pageSize.value = newSize
  page.value = 1
  handlePageChange(1)
}

const goBack = () => {
  router.back()
}

const goToPoem = (poemId: string) => {
  const poem = poemsList.value.find(p => p.id === poemId)
  if (poem?.chunk_id !== undefined) {
    router.push({
      path: `/poems/${poemId}`,
      query: { chunk_id: poem.chunk_id.toString() }
    })
  } else {
    router.push(`/poems/${poemId}`)
  }
}

const goToPoems = () => {
  router.push('/poems')
}

const goToAuthor = (author: string) => {
  router.push(`/authors/${encodeURIComponent(author)}`)
}

const getDynastyColor = (dynasty: string): string => {
  const colors: Record<string, string> = {
    '唐': '#B45309',
    '宋': '#1E40AF',
    '元': '#047857',
    '明': '#B45309',
    '清': '#7C3AED',
    '近现代': '#DC2626'
  }
  return colors[dynasty] || '#5C5244'
}

// FastText ONNX 相似词（用于底部词云）
const { init: ftInit, getSimilar } = useFasttextOnnx()
const cloudWords = ref<Array<{ word: string; count: number; rank: number }>>([])
const cloudLoading = ref(false)
const cloudError = ref('')
let ftInitialized = false
async function ensureFtInit() {
  if (ftInitialized) return true
  cloudLoading.value = true
  const r = await ftInit()
  cloudLoading.value = false
  if (r.ok) {
    ftInitialized = true
    return true
  }
  cloudError.value = '模型初始化失败或未部署 onnxruntime-web，无法计算相似词。'
  return false
}

async function loadSimilarWords() {
  cloudError.value = ''
  cloudWords.value = []
  if (!keyword.value || !keyword.value.trim()) return
  const ok = await ensureFtInit()
  if (!ok) return
  cloudLoading.value = true
  try {
    const sims = await getSimilar(keyword.value.trim(), 80)
    cloudWords.value = sims.map((s, i) => ({ word: s.token, count: Math.max(1, Math.round(s.score * 1000)), rank: i + 1 }))
  } catch (e: any) {
    cloudError.value = e?.message || String(e)
  } finally {
    cloudLoading.value = false
  }
}

onMounted(() => {
  loadData()
})

watch(keyword, () => {
  loadData()
})
</script>

<template>
  <div class="keyword-detail-view">
    <NBackTop :right="40" :bottom="40" />

    <NPageHeader @back="goBack">
      <template #title>
        <span class="page-title">关键词详情</span>
      </template>
      <template #extra>
        <NSpace>
          <NButton @click="goToPoems">
            全部诗词
          </NButton>
        </NSpace>
      </template>
    </NPageHeader>

    <NCard class="keyword-header-card">
      <div class="keyword-header">
        <div class="keyword-title-section">
          <h1 class="keyword-title">{{ keyword }}</h1>
          <div class="keyword-subtitle">
            <NTag type="primary" size="large">
              {{ poemIds.length }} 篇诗词
            </NTag>
          </div>
        </div>
      </div>
    </NCard>

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard label="出现频次" :value="wordCount !== null ? wordCount.toLocaleString() : '-'"
          :prefix-icon="TrendingUpOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="词频排名" :value="wordRank !== null ? `#${wordRank.toLocaleString()}` : '-'"
          :prefix-icon="TextOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="收录诗词" :value="`${poemIds.length.toLocaleString()} / ${totalPoems.toLocaleString()}`"
          :prefix-icon="BookOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="朝代分布" :value="`${dynastyStats.length} 个`" :prefix-icon="ListOutline" />
      </NGridItem>
    </NGrid>

    <NSpin :show="isLoading" size="large">
      <NEmpty v-if="!isLoading && poemsList.length === 0" :description="`未找到包含「${keyword}」的诗词`">
        <template #extra>
          <NButton @click="goToPoems">返回诗词列表</NButton>
        </template>
      </NEmpty>

      <template v-else>
        <NCard title="相似词词云" class="wordcloud-card">
          <div class="wordcloud-container">
            <div v-if="cloudLoading" class="status">
              <NSpin size="small" />
              <span style="margin-left: 8px">基于 FastText ONNX 模型，正在计算相似词…</span>
            </div>
             <NEmpty v-else-if="cloudError === 'Unknown token'" description="词汇出现次数低，无法计算相似词。">
            </NEmpty>
            <WordCloud v-else-if="cloudWords.length > 0" :words="cloudWords" :width="700" :height="350"
              :title="`「${keyword}」的相似词词云`" />
            <NEmpty v-else description="未加载到相似词">
            </NEmpty>
          </div>
        </NCard>

        <NCard v-if="dynastyStats.length > 0 || genreStats.length > 0" title="朝代和体裁分布" class="stats-card">
          <div class="charts-container">
            <div class="chart-item">
              <div ref="dynastyChartRef" class="chart"></div>
            </div>
            <div class="chart-item">
              <div ref="genreChartRef" class="chart"></div>
            </div>
          </div>
        </NCard>

        <NCard title="包含该关键词的诗词" class="poems-card">
          <PoemList :poems="allPoems" v-model:page="page" v-model:page-size="pageSize"
            :show-pagination="true" :grid-view="false" @view-poem="(poem) => goToPoem(poem.id)" />
        </NCard>
      </template>
    </NSpin>
  </div>
</template>

<style scoped>
.keyword-detail-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.keyword-header-card {
  margin-top: 24px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.keyword-header {
  text-align: center;
  padding: 24px 0;
}

.keyword-title {
  margin: 0 0 16px;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 42px;
  font-weight: 700;
  color: #8b2635;
  line-height: 1.4;
}

.keyword-subtitle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.stats-grid {
  margin-bottom: 24px;
}



.stats-card {
  margin-bottom: 24px;
}

.stats-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-label {
  width: 60px;
  font-weight: 500;
  flex-shrink: 0;
}

.stat-bar-container {
  flex: 1;
  height: 20px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.stat-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.stat-count {
  width: 40px;
  text-align: right;
  font-weight: 500;
  color: #666;
  flex-shrink: 0;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.poems-card {
  margin-top: 24px;
}

.wordcloud-card {
  margin-bottom: 24px;
}

.wordcloud-container {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.status {
  display: flex;
  align-items: center;
  color: #666;
  font-size: 14px;
}

.error-container {
  text-align: center;
  padding: 16px;
}

.charts-container {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.chart-item {
  flex: 1;
  min-width: 300px;
  max-width: 450px;
}

.chart {
  width: 100%;
  height: 250px;
}



@media (max-width: 768px) {
  .keyword-title {
    font-size: 32px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
