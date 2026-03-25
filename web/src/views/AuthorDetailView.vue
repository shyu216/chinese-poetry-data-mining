<!--
  文件: web/src/views/AuthorDetailView.vue
  说明: 作者详情页，展示作者统计信息、代表作品列表与相关检索结果；协调多个 composable（作者、诗文、索引）来拼接页面数据。

  数据管线:
    - 输入: 路由参数 `name` 触发 `useAuthorsV2.getAuthorByName()` 获取作者元信息。
    - 聚合: 使用 `usePoemsV2` 按 id 批量获取诗文详情，并用 `useSearchIndexV2` 获取摘要/关键词用于列表展示。
    - 分页/渲染: 在客户端对作者的诗文做分页（`poemsPage`, `poemsPageSize`），并将子组件（`PoemList` / `StatsCard`）渲染所需数据传下去。

  复杂度:
    - 数据查询: 获取作者与诗文为常数次数的网络/缓存请求，内部遍历/拼接为 O(n)，n = 作者诗数。
    - 排序/过滤: 若进行排序为 O(n log n)；分页渲染为 O(k)，k = 单页条数。
    - 空间: 客户端缓存作者诗文与映射表（`poemChunkMap`）使空间复杂度为 O(n)。

  使用技术/要点:
    - 组合式 composables (`useAuthorsV2`, `usePoemsV2`, `useSearchIndexV2`) 将数据获取/缓存与 UI 分离。
    - 分页在客户端执行以减少路由切换请求，但父组件负责追加数据（拉取更多时触发）。
    - 使用 `Map` 存储 poem_id -> chunk_id 提高查找性能。

  潜在问题/改进建议:
    - 若作者诗量极大（数千/数万），客户端一次性拉取并缓存会导致内存与渲染压力，建议按需分片加载或服务端分页。
    - 多个 composable 间的同步/错误处理需统一（重试、幂等、超时），当前实现缺少集中错误策略。
    - 对大数组的排序/过滤应避免在主线程阻塞，可考虑 Web Worker 分片处理或后端排序。
    - 图片/资源未懒加载可能影响首屏；需为诗文列表添加占位与懒加载策略。
-->
<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useSearchIndexV2 } from '@/composables/useSearchIndexV2'
import type { AuthorStats } from '@/composables/types'
import type { PoemDetail } from '@/composables/types'
import {
  NCard, NEmpty, NTag, NButton, NSpace,
  NDivider, NList, NListItem, NThing,
  NGrid, NGridItem, NProgress, NPagination
} from 'naive-ui'
import {
  PersonOutline, BookOutline,
  ChevronForwardOutline, MedalOutline, BarChartOutline,
  TextOutline
} from '@vicons/ionicons5'
import { PageHeader } from '@/components/layout'
import { StatsCard } from '@/components/display'
import PoemList from '@/components/display/PoemList.vue'
import { useLoading } from '@/composables/useLoading'

const loading = useLoading()
const route = useRoute()
const router = useRouter()
const { getAuthorByName } = useAuthorsV2()
const { getPoemById, getPoemsByIds } = usePoemsV2()
const { getPoemSummariesByIds } = useSearchIndexV2()

const authorName = computed(() => route.params.name as string)
const author = ref<AuthorStats | null>(null)
const poems = ref<PoemDetail[]>([])
const poemChunkMap = ref<Map<string, number>>(new Map()) // 存储 poem_id -> chunk_id 映射
const isLoading = ref(true)
const poemsLoading = ref(false)

const poemsPage = ref(1)
const poemsPageSize = ref(20)

const paginatedPoems = computed(() => {
  const start = (poemsPage.value - 1) * poemsPageSize.value
  const end = start + poemsPageSize.value
  return poems.value.slice(start, end)
})

const totalPoemsPages = computed(() =>
  Math.ceil(poems.value.length / poemsPageSize.value)
)

onMounted(async () => {
  await loadAuthorData()
})

watch(() => route.params.name, async (newName, oldName) => {
  if (newName !== oldName && newName) {
    poemsPage.value = 1
    await loadAuthorData()
  }
})

const loadAuthorData = async () => {
  // 步骤 1: 初始化
  loading.startBlocking('诗人详情', '正在加载诗人数据...')

  try {
    loading.updatePhase('metadata', '正在加载诗人信息...')
    loading.updateProgress(0, 2)
    author.value = await getAuthorByName(authorName.value)

    if (author.value && author.value.poem_ids.length > 0) {
      loading.updateProgress(1, 2, `正在加载 ${author.value.poem_ids.length} 首作品...`)
      await loadAuthorPoems()
    }

    loading.updatePhase('complete', '数据加载完成')
    loading.updateProgress(2, 2)
    setTimeout(() => loading.finish(), 300)
  } catch (e) {
    loading.error('加载失败')
    console.error('Error loading author:', e)
  }
}

const loadAuthorPoems = async () => {
  if (!author.value) return
  poemsLoading.value = true
  poems.value = []

  const totalPoems = author.value.poem_ids.length
  const loadedPoems: PoemDetail[] = []

  try {
    // 使用批量加载优化：先获取诗词摘要（含 chunk_id），再批量加载详情
    const batchSize = 50

    for (let i = 0; i < author.value.poem_ids.length; i += batchSize) {
      const batchIds = author.value.poem_ids.slice(i, i + batchSize)

      // 1. 从 poem_index 获取诗词摘要（包含 chunk_id）
      const poemSummaries = await getPoemSummariesByIds(batchIds)

      // 2. 提取 chunk_ids 用于批量加载，并存储到映射表
      const idsWithChunkIds: string[] = []
      const chunkIds: number[] = []

      for (const [id, summary] of poemSummaries.entries()) {
        if (summary.chunk_id !== undefined) {
          idsWithChunkIds.push(id)
          chunkIds.push(summary.chunk_id)
          poemChunkMap.value.set(id, summary.chunk_id)
        }
      }

      // 3. 使用 chunk_id 批量加载诗词详情
      let batchResults: PoemDetail[] = []

      if (idsWithChunkIds.length === batchIds.length) {
        // 所有诗词都有 chunk_id，使用优化批量加载
        batchResults = await getPoemsByIds(idsWithChunkIds, chunkIds)
      } else {
        // 部分诗词没有 chunk_id，回退到逐个加载
        console.warn(`[AuthorDetail] Some poems missing chunk_id, falling back to individual loading`)
        const individualResults = await Promise.all(
          batchIds.map(id => getPoemById(id))
        )
        batchResults = individualResults.filter((p): p is PoemDetail => p !== null)
      }

      // 保持原始顺序
      for (const id of batchIds) {
        const poem = batchResults.find(p => p.id === id)
        if (poem) {
          loadedPoems.push(poem)
        }
      }

      // 更新进度
      const currentProgress = Math.min(i + batchSize, totalPoems)
      loading.updateProgress(currentProgress, totalPoems, `已加载 ${currentProgress}/${totalPoems} 首...`)
    }

    poems.value = loadedPoems
  } catch (e) {
    console.error('Error loading poems:', e)
  } finally {
    poemsLoading.value = false
  }
}

const goBack = () => {
  router.back()
}

const goToPoem = (id: string) => {
  const chunkId = poemChunkMap.value.get(id)
  if (chunkId !== undefined) {
    router.push({
      path: `/poems/${id}`,
      query: { chunk_id: chunkId.toString() }
    })
  } else {
    router.push(`/poems/${id}`)
  }
}

const goToAuthors = () => {
  router.push('/authors')
}

const dynastyColors: Record<string, string> = {
  '唐': 'error',
  '宋': 'info',
  '元': 'success',
  '明': 'warning',
  '清': 'purple'
}

const getTopPoemType = () => {
  if (!author.value) return '-'
  const entries = Object.entries(author.value.poem_type_counts)
  if (entries.length === 0) return '-'
  const sorted = entries.sort((a, b) => b[1] - a[1])
  return sorted[0]?.[0] || '-'
}

const getTypeDistribution = () => {
  if (!author.value) return []
  const typeCounts = author.value.poem_type_counts
  const total = Object.values(typeCounts).reduce((a, b) => a + b, 0)
  const entries = Object.entries(typeCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  return entries.map(([type, count]) => ({
    type,
    count,
    percentage: Math.round((count / total) * 100)
  }))
}
</script>

<template>
  <div class="author-detail-view">
    <PageHeader
      title="作者详情"
      subtitle="查看作者详细信息及作品列表"
      :icon="PersonOutline"
    />

    <NEmpty v-if="!loading && !author" description="未找到该诗人信息">
      <template #extra>
        <NButton @click="goToAuthors">返回诗人列表</NButton>
      </template>
    </NEmpty>

    <template v-else-if="author">
        <NCard class="author-header-card">
          <div class="author-header">
            <div class="author-avatar">
              <span class="avatar-text">{{ author.author.charAt(0) }}</span>
            </div>
            <div class="author-info">
              <h1 class="author-name">{{ author.author }}</h1>
              <div class="author-meta">
                <NTag type="primary" size="large">
                  <template #icon>
                    <BookOutline />
                  </template>
                  {{ author.poem_count }} 首诗词
                </NTag>
                <NTag v-if="getTopPoemType() !== '-'" type="info" size="large">
                  <template #icon>
                    <TextOutline />
                  </template>
                  擅长 {{ getTopPoemType() }}
                </NTag>
              </div>
            </div>
          </div>
        </NCard>

        <NGrid :cols="3" :x-gap="16" :y-gap="16" class="stats-grid">
          <NGridItem>
            <StatsCard
              label="诗词总数"
              :value="author.poem_count"
              :prefix-icon="BookOutline"
            />
          </NGridItem>
          <NGridItem>
            <StatsCard
              label="诗词体裁"
              :value="Object.keys(author.poem_type_counts).length"
              :prefix-icon="TextOutline"
            />
          </NGridItem>
          <NGridItem>
            <StatsCard
              label="相似诗人"
              :value="author.similar_authors.length"
              :prefix-icon="PersonOutline"
            />
          </NGridItem>
        </NGrid>

        <NGrid :cols="2" :x-gap="16" :y-gap="16" class="content-grid">
          <NGridItem>
            <NCard title="诗词体裁分布" class="distribution-card">
              <div class="type-distribution">
                <div
                  v-for="item in getTypeDistribution()"
                  :key="item.type"
                  class="type-bar"
                >
                  <span class="type-label">{{ item.type }}</span>
                  <NProgress
                    type="line"
                    :percentage="item.percentage"
                    :show-indicator="false"
                    :height="8"
                    status="success"
                  />
                  <span class="type-count">{{ item.count }}首</span>
                </div>
              </div>
            </NCard>
          </NGridItem>

          <NGridItem>
            <NCard title="相似诗人" class="similar-card">
              <NSpace v-if="author.similar_authors.length > 0" wrap>
                <NButton
                  v-for="similar in author.similar_authors.slice(0, 8)"
                  :key="similar.author"
                  size="small"
                  @click="$router.push(`/authors/${encodeURIComponent(similar.author)}`)"
                >
                  {{ similar.author }}
                  <span class="similarity-score">({{ (similar.similarity * 100).toFixed(0) }}%)</span>
                </NButton>
              </NSpace>
              <NEmpty v-else description="暂无相似诗人推荐" />
            </NCard>
          </NGridItem>
        </NGrid>

        <NCard title="作品列表" class="poems-card">
          <NEmpty v-if="!poemsLoading && poems.length === 0" description="暂无诗词作品" />
          <template v-else>
            <PoemList
              :poems="poems"
              v-model:page="poemsPage"
              v-model:page-size="poemsPageSize"
              :show-pagination="true"
              :grid-view="false"
              @view-poem="(poem) => goToPoem(poem.id)"
            />
          </template>
        </NCard>
      </template>
  </div>
</template>

<style scoped>
.author-detail-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.author-header-card {
  margin-top: 24px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.author-header {
  display: flex;
  align-items: center;
  gap: 24px;
}

.author-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b2635 0%, #c41e3a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-size: 36px;
  font-weight: 600;
  color: #fff;
}

.author-info {
  flex: 1;
}

.author-name {
  margin: 0 0 12px;
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
}

.author-meta {
  display: flex;
  gap: 12px;
}

.stats-grid {
  margin-bottom: 24px;
}

.content-grid {
  margin-bottom: 24px;
}

.distribution-card,
.similar-card {
  height: 100%;
}

.type-distribution {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-label {
  font-size: 14px;
  color: #666;
  width: 80px;
  flex-shrink: 0;
}

.type-count {
  font-size: 13px;
  color: #999;
  width: 60px;
  text-align: right;
  flex-shrink: 0;
}

.similarity-score {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

.poems-card {
  margin-top: 24px;
}

.poem-title {
  font-size: 16px;
  font-weight: 500;
  color: #2c3e50;
}

.poem-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.arrow-icon {
  width: 16px;
  height: 16px;
  color: #999;
  transition: all 0.2s ease;
}

:deep(.n-list-item):hover .arrow-icon {
  color: #8b2635;
  transform: translateX(4px);
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .author-header {
    flex-direction: column;
    text-align: center;
  }

  .author-meta {
    justify-content: center;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
