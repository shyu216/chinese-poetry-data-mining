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
import PageHeader from '@/components/PageHeader.vue'
import StatsCard from '@/components/StatsCard.vue'
import { useLoading } from '@/composables/useLoading'

const globalLoading = useLoading()
const route = useRoute()
const router = useRouter()
const { getAuthorByName } = useAuthorsV2()
const { getPoemById, getPoemsByIds } = usePoemsV2()
const { getPoemSummariesByIds } = useSearchIndexV2()

const authorName = computed(() => route.params.name as string)
const author = ref<AuthorStats | null>(null)
const poems = ref<PoemDetail[]>([])
const poemChunkMap = ref<Map<string, number>>(new Map()) // 存储 poem_id -> chunk_id 映射
const loading = ref(true)
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
  const taskId = globalLoading.startBlocking(
    '载入诗人详情',
    '正在加载诗人信息...',
    5
  )

  loading.value = true
  try {
    author.value = await getAuthorByName(authorName.value)
    if (author.value && author.value.poem_ids.length > 0) {
      globalLoading.update(taskId, {
        description: `正在加载诗词作品 (0/${author.value.poem_ids.length})...`,
        progress: 50
      })
      await loadAuthorPoems(taskId)
    }
    globalLoading.update(taskId, { description: '加载完成', progress: 100 })
    setTimeout(() => globalLoading.finish(taskId), 300)
  } catch (e) {
    globalLoading.update(taskId, { description: '加载失败' })
    console.error('Error loading author:', e)
  } finally {
    loading.value = false
  }
}

const loadAuthorPoems = async (taskId?: string) => {
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
      const progress = Math.round((Math.min(i + batchSize, totalPoems) / totalPoems) * 50) + 50
      const description = `正在加载诗词作品 (${Math.min(i + batchSize, totalPoems)}/${totalPoems})...`

      if (taskId) {
        globalLoading.update(taskId, { description, progress })
      }
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
      title="诗人详情"
      subtitle="查看诗人详细信息及作品列表"
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
            <NList hoverable clickable>
              <NListItem
                v-for="poem in paginatedPoems"
                :key="poem.id"
                @click="goToPoem(poem.id)"
              >
                <NThing>
                  <template #header>
                    <span class="poem-title">{{ poem.title || '无题' }}</span>
                  </template>
                  <template #description>
                    <div class="poem-meta">
                      <NTag
                        v-if="poem.dynasty"
                        :type="dynastyColors[poem.dynasty] as any"
                        size="small"
                      >
                        {{ poem.dynasty }}
                      </NTag>
                      <NTag v-if="poem.genre" type="info" size="small">
                        {{ poem.genre }}
                      </NTag>
                      <NTag v-if="poem.poem_type" type="success" size="small">
                        {{ poem.poem_type }}
                      </NTag>
                    </div>
                  </template>
                  <template #header-extra>
                    <ChevronForwardOutline class="arrow-icon" />
                  </template>
                </NThing>
              </NListItem>
            </NList>

            <div v-if="totalPoemsPages > 1" class="pagination-wrapper">
              <NPagination
                v-model:page="poemsPage"
                :page-count="totalPoemsPages"
                :page-size="poemsPageSize"
                show-size-picker
                :page-sizes="[10, 20, 50, 100]"
                @update:page-size="poemsPageSize = $event"
              />
            </div>
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
