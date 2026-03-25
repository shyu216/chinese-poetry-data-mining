<!--
  @overview
  file: web/src/views/KeywordDetailView.vue
  category: frontend-page
  tech: Vue 3 + TypeScript + Vue Router + Naive UI + Plotly
  solved: 承载页面级交互、筛选、展示与路由联动
  data_source: 组合式状态与组件内部状态
  data_flow: 状态输入 -> 组件渲染(NBackTop, NPageHeader) -> 路由联动
  complexity: 常见查询/筛选 O(n)，排序 O(n log n)，空间复杂度常见 O(n)
  unique: 核心导出: newPlot, react, purge；关键函数: loadData, loadRemainingPoems, renderCharts, handlePageChange；主渲染组件: NBackTop, NPageHeader
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useKeywordIndex } from '@/composables/useKeywordIndex'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useSearchIndexV2 } from '@/composables/useSearchIndexV2'
import { useWordcountV2 } from '@/composables/useWordcountV2'
import type { PoemSummary } from '@/composables/types'
import {
  NCard, NSpin, NEmpty, NTag, NButton, NSpace,
  NPageHeader, NGrid, NGridItem, NBackTop, NPagination
} from 'naive-ui'
import { StatsCard } from '@/components/display'
import PoemList from '@/components/display/PoemList.vue'
import { ArrowBackOutline, SearchOutline, BookOutline,
  TextOutline, TrendingUpOutline, ListOutline
} from '@vicons/ionicons5'
import { useLoading } from '@/composables/useLoading'
import * as Plotly from 'plotly.js-dist-min'
// 为 Plotly 添加类型声明
declare module 'plotly.js-dist-min' {
  export interface PlotlyHTMLElement extends HTMLElement {}
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
const poemsV2 = usePoemsV2()
const searchIndexV2 = useSearchIndexV2()
const wordcountV2 = useWordcountV2()

const keyword = computed(() => route.params.word as string)
const poemIds = ref<string[]>([])
const poems = ref<PoemSummary[]>([])
const isLoading = ref(true)
const wordRank = ref<number | null>(null)
const wordCount = ref<number | null>(null)

// 分页相关
const page = ref(1)
const pageSize = ref(24)
const loadingPoems = ref(false)

const totalPoems = computed(() => poemsV2.totalPoems.value)

const dynastyStats = computed(() => {
  const targetPoems = allPoems.value.length > 0 ? allPoems.value : poems.value
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
  const targetPoems = allPoems.value.length > 0 ? allPoems.value : poems.value
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
  const results: PoemSummary[] = []

  for (let i = 0; i < ids.length; i += batchSize) {
    const batch = ids.slice(i, i + batchSize)
    console.log(`[KeywordDetail] Batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(ids.length/batchSize)}: loading ${batch.length} poems`)

    // 1. 先从 poem_index 获取诗词摘要（包含 chunk_id）
    const step1Start = Date.now()
    const poemSummaries = await searchIndexV2.getPoemSummariesByIds(batch)
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

    if (idsWithChunkIds.length === batch.length) {
      // 所有诗词都有 chunk_id，使用优化批量加载
      console.log(`[KeywordDetail]   -> Using optimized batch loading with ${chunkIds.length} chunks`)
      const poemsWithDetails = await poemsV2.getPoemsByIds(idsWithChunkIds, chunkIds)
      // 保持原始顺序
      batchResults = batch.map(id => poemsWithDetails.find(p => p.id === id) || null)
    } else {
      // 部分诗词没有 chunk_id，回退到逐个加载
      console.warn(`[KeywordDetail] Some poems missing chunk_id (${idsWithChunkIds.length}/${batch.length}), falling back to individual loading`)
      batchResults = await Promise.all(batch.map(id => poemsV2.getPoemById(id)))
    }
    console.log(`[KeywordDetail]   -> Loaded ${batchResults.filter(p => p !== null).length} poems in ${Date.now() - step3Start}ms`)

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
      poems.value = results.slice(0, pageSize.value)
    }
  }

  console.log(`[KeywordDetail] loadPoemsBatch DONE: ${results.length} poems in ${Date.now() - batchStartTime}ms`)
  return results
}

const loadData = async () => {
  console.log(`[KeywordDetail] loadData START for keyword: "${keyword.value}"`)
  const startTime = Date.now()

  // 步骤 1: 初始化 - 开始 blocking loading
    loading.startBlocking('关键词详情', `查询"${keyword.value}"...`)
    isLoading.value = true
    loadingPoems.value = true
    poems.value = []
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

    poems.value = firstPageResults

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
      allPoems.value = poems.value
    }

    // 后台获取词频统计
    wordcountV2.getTopWords(10000).then(allWords => {
      const foundWord = allWords.find(w => w.word === keyword.value)
      if (foundWord) {
        wordRank.value = foundWord.rank
        wordCount.value = foundWord.count
      }
    })
  } catch (e) {
    console.error('[KeywordDetail] ERROR in loadData:', e)
    loading.error('加载失败')
    isLoading.value = false
  } finally {
    console.log(`[KeywordDetail] loadData FINALLY, total time: ${Date.now() - startTime}ms`)
  }
}

// 后台加载剩余诗词
const allPoems = ref<PoemSummary[]>([])
const loadRemainingPoems = async (ids: string[]) => {
  console.log(`[KeywordDetail] loadRemainingPoems START: ${ids.length} poems`)
  const startTime = Date.now()
  try {
    // 后台加载，不更新UI，避免覆盖当前页
    const remaining = await loadPoemsBatch(ids, false)
    allPoems.value = [...poems.value, ...remaining]
    loadingPoems.value = false
    loading.finish()
    console.log(`[KeywordDetail] loadRemainingPoems DONE: ${allPoems.value.length} total poems in ${Date.now() - startTime}ms`)
    // 数据加载完成后更新图表
    setTimeout(() => {
      renderCharts()
    }, 100)
  } catch (e) {
    console.error('[KeywordDetail] ERROR in loadRemainingPoems:', e)
    loadingPoems.value = false
    loading.finish()
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
    const targetPoems = allPoems.value.length > 0 ? allPoems.value : poems.value
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
    const targetPoems = allPoems.value.length > 0 ? allPoems.value : poems.value
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
    poems.value = allPoems.value.slice(start, end)
    return
  }
  
  // 否则按需加载 - 使用 chunk_id 优化
  const pageIds = poemIds.value.slice(start, end)
  const pageResults = await loadPoemsBatch(pageIds, true)
  
  poems.value = pageResults
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
  const poem = poems.value.find(p => p.id === poemId)
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
        <StatsCard 
          label="出现频次" 
          :value="wordCount !== null ? wordCount.toLocaleString() : '-'" 
          :prefix-icon="TrendingUpOutline" 
        />
      </NGridItem>
      <NGridItem>
        <StatsCard 
          label="词频排名" 
          :value="wordRank !== null ? `#${wordRank.toLocaleString()}` : '-'" 
          :prefix-icon="TextOutline" 
        />
      </NGridItem>
      <NGridItem>
        <StatsCard 
          label="收录诗词" 
          :value="`${poemIds.length.toLocaleString()} / ${totalPoems.toLocaleString()}`" 
          :prefix-icon="BookOutline" 
        />
      </NGridItem>
      <NGridItem>
        <StatsCard 
          label="朝代分布" 
          :value="`${dynastyStats.length} 个`" 
          :prefix-icon="ListOutline" 
        />
      </NGridItem>
    </NGrid>

    <NSpin :show="isLoading" size="large">
      <NEmpty v-if="!isLoading && poems.length === 0" :description="`未找到包含「${keyword}」的诗词`">
        <template #extra>
          <NButton @click="goToPoems">返回诗词列表</NButton>
        </template>
      </NEmpty>

      <template v-else>
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
          <PoemList
            :poems="poems"
            :total="poemIds.length"
            v-model:page="page"
            v-model:page-size="pageSize"
            :show-pagination="true"
            :grid-view="false"
            @view-poem="(poem) => goToPoem(poem.id)"
          />
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
