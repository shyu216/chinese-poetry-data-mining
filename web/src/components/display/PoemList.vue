<!--
  @overview
  file: web/src/components/display/PoemList.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Vue Router + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props；组件事件
  data_flow: 数据/事件输入 -> 组件渲染(DynastyBadge, ChevronForwardOutline, NList) -> 事件回传与路由跳转
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: handlePoemClick, handlePageChange, handlePageSizeChange；主渲染组件: DynastyBadge, ChevronForwardOutline, NList, NListItem
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { PoemSummary } from '@/composables/types'
import { NEmpty, NPagination, NList, NListItem, NThing, NTag } from 'naive-ui'
import { ChevronForwardOutline } from '@vicons/ionicons5'
import DynastyBadge from '@/components/ui/badge/DynastyBadge.vue'

const props = defineProps<{
  poems: PoemSummary[]
  loading?: boolean
  total?: number
  page?: number
  pageSize?: number
  showPagination?: boolean
  gridView?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:page', value: number): void
  (e: 'update:pageSize', value: number): void
  (e: 'viewPoem', poem: PoemSummary): void
}>()

const router = useRouter()

const currentPage = computed({
  get: () => props.page || 1,
  set: (value) => emit('update:page', value)
})

const currentPageSize = computed({
  get: () => props.pageSize || 24,
  set: (value) => emit('update:pageSize', value)
})

const totalPages = computed(() => {
  const total = props.total || props.poems.length
  return Math.ceil(total / currentPageSize.value)
})

const paginatedPoems = computed(() => {
  if (props.total !== undefined) {
    // 搜索模式下，数据已经分页
    return props.poems
  }
  // 列表模式下，内存分页
  const start = (currentPage.value - 1) * currentPageSize.value
  const end = start + currentPageSize.value
  return props.poems.slice(start, end)
})

const handlePoemClick = (poem: PoemSummary) => {
  emit('viewPoem', poem)
  if (poem.chunk_id !== undefined) {
    router.push({
      path: `/poems/${poem.id}`,
      query: { chunk_id: poem.chunk_id.toString() }
    })
  } else {
    router.push(`/poems/${poem.id}`)
  }
}

const handlePageChange = (page: number) => {
  emit('update:page', page)
}

const handlePageSizeChange = (size: number) => {
  emit('update:pageSize', size)
  emit('update:page', 1)
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
</script>

<template>
  <div class="poem-list">
    <!-- 网格视图 -->
    <div v-if="gridView && poems.length > 0" class="poems-grid">
      <article
        v-for="poem in paginatedPoems"
        :key="poem.id"
        class="poem-card"
        @click="handlePoemClick(poem)"
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

    <!-- 列表视图 -->
    <NList v-else-if="poems.length > 0" hoverable clickable class="poems-list">
      <NListItem
        v-for="poem in paginatedPoems"
        :key="poem.id"
        @click="handlePoemClick(poem)"
      >
        <NThing>
          <template #header>
            <span class="poem-title">{{ poem.title || '无题' }}</span>
          </template>
          <template #description>
            <div class="poem-meta">
              <NTag
                v-if="poem.dynasty"
                :style="{ color: getDynastyColor(poem.dynasty) }"
                size="small"
              >
                {{ poem.dynasty }}
              </NTag>
              <NTag v-if="poem.genre" type="info" size="small">
                {{ poem.genre }}
              </NTag>
              <span class="author">{{ poem.author }}</span>
            </div>
          </template>
          <template #header-extra>
            <ChevronForwardOutline class="arrow-icon" />
          </template>
        </NThing>
      </NListItem>
    </NList>

    <!-- 空状态 -->
    <NEmpty v-else :description="loading ? '加载中...' : '暂无诗词数据'" />

    <!-- 分页 -->
    <div v-if="showPagination && totalPages > 1" class="pagination-wrapper">
      <NPagination
        v-model:page="currentPage"
        :page-count="totalPages"
        :page-size="currentPageSize"
        show-size-picker
        :page-sizes="[12, 24, 48, 96]"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>
  </div>
</template>

<style scoped>
.poem-list {
  width: 100%;
}

/* 网格视图样式 */
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

/* 列表视图样式 */
.poems-list {
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
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

.poem-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.author {
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

.poems-list :deep(.n-list-item):hover .arrow-icon {
  opacity: 1;
  color: var(--color-seal, #8b2635);
  transform: translateX(2px);
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .poems-grid {
    grid-template-columns: 1fr;
  }
}
</style>