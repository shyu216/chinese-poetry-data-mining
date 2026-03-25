<!--
  文件: web/src/components/author/AuthorList.vue
  说明: 作者列表组件，接收父组件分页/全集作者数据，通过列表渲染卡片项并提供“加载更多”事件。

  数据管线:
    - 输入: 通过 `props.authors` 接收当前页/当前已加载的作者数组，`props.total` 表示总量。
    - 处理: 列表渲染（`v-for`），局部计算（`hasMore`），并通过 `emit('loadMore')` 请求更多数据。
    - 输出: 触发 `loadMore` 事件由父组件处理，请求并追加新数据到 `authors`。

  复杂度:
    - 渲染为 O(n)（n 为当前 authors.length），每次加载更多会增加渲染成本。
    - 内存: 客户端持有当前已加载条目，空间复杂度 O(k)，k 为已加载条数。

  关键技术/要点:
    - 使用 Naive UI 的列表与骨架组件（NList, NSpin, NEmpty）简化加载态与空态处理。
    - 通过 `encodeURIComponent` 构造路由参数以避免特殊字符问题。

  潜在问题:
    - 父组件若直接用大数组渲染且无虚拟化，会导致大量 DOM 耗时和内存消耗。
    - `loadMore` 事件未防抖或幂等控制，重复快速点击可能触发多次请求。
    - 列表 key 使用 `author.author`，若存在重名会导致渲染复用问题，建议使用稳定唯一 ID。
    - 无明确错误/空态重试策略，网络失败时用户体验需要补充。
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NList, NListItem, NThing, NEmpty, NSpin, NButton, NAvatar } from 'naive-ui'
import { RefreshOutline, PersonOutline } from '@vicons/ionicons5'
import { DynastyBadge } from '@/components/ui/badge'

export interface AuthorListItem {
  author: string
  dynasty: string
  poemCount: number
  avatar?: string
  rank?: number
  tags?: string[]
}

interface Props {
  authors: AuthorListItem[]
  loading?: boolean
  emptyText?: string
  showDynasty?: boolean
  showPoemCount?: boolean
  pageSize?: number
  total?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  emptyText: '暂无诗人',
  showDynasty: true,
  showPoemCount: true,
  pageSize: 20,
  total: 0
})

const emit = defineEmits<{
  loadMore: []
}>()

const router = useRouter()

const hasMore = computed(() => {
  return props.total > props.authors.length
})

const getInitials = (name: string) => {
  return name.slice(0, 2)
}

const goToAuthor = (author: string) => {
  router.push(`/author/${encodeURIComponent(author)}`)
}

const goToDynasty = (dynasty: string, e: Event) => {
  e.stopPropagation()
  router.push(`/authors?dynasty=${encodeURIComponent(dynasty)}`)
}

const handleLoadMore = () => {
  emit('loadMore')
}
</script>

<template>
  <div class="author-list">
    <NSpin :show="loading" size="medium">
      <NEmpty v-if="!loading && authors.length === 0" :description="emptyText" />
      
      <NList v-else clickable class="list-container">
        <NListItem 
          v-for="author in authors" 
          :key="author.author"
          class="author-item"
          @click="goToAuthor(author.author)"
        >
          <NThing>
            <template #avatar>
              <div class="author-avatar-wrap">
                <NAvatar 
                  v-if="author.avatar" 
                  :src="author.avatar" 
                  :size="48" 
                  round
                />
                <NAvatar v-else :size="48" round>
                  {{ getInitials(author.author) }}
                </NAvatar>
                <span v-if="author.rank" class="rank-badge">{{ author.rank }}</span>
              </div>
            </template>

            <template #header>
              <div class="author-header">
                <span class="author-name">{{ author.author }}</span>
                <DynastyBadge 
                  v-if="showDynasty" 
                  :dynasty="author.dynasty" 
                  size="small" 
                  @click="goToDynasty(author.dynasty, $event)"
                />
              </div>
            </template>

            <template #description>
              <div v-if="showPoemCount" class="author-desc">
                <PersonOutline class="desc-icon" />
                <span>{{ author.poemCount }} 首</span>
              </div>
            </template>

            <template #footer v-if="author.tags?.length">
              <div class="author-tags">
                <span 
                  v-for="tag in author.tags.slice(0, 2)" 
                  :key="tag" 
                  class="tag"
                >
                  {{ tag }}
                </span>
              </div>
            </template>
          </NThing>
        </NListItem>
      </NList>

      <div v-if="hasMore" class="load-more">
        <NButton 
          quaternary 
          :loading="loading" 
          @click="handleLoadMore"
        >
          <template #icon>
            <RefreshOutline />
          </template>
          加载更多
        </NButton>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.author-list {
  width: 100%;
}

.list-container {
  background: transparent;
}

.author-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.author-item:hover {
  border-color: var(--color-seal, #8b2635);
  background: rgba(139, 38, 53, 0.02);
}

.author-avatar-wrap {
  position: relative;
}

.author-avatar-wrap :deep(.n-avatar) {
  background: linear-gradient(135deg, var(--color-seal, #8b2635), #a63d4d);
  color: #fff;
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  font-weight: 600;
}

.rank-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--color-seal, #8b2635);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.author-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.author-desc {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.desc-icon {
  font-size: 14px;
}

.author-tags {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.tag {
  padding: 2px 8px;
  font-size: 12px;
  color: #B45309;
  background: rgba(180, 83, 9, 0.08);
  border-radius: 4px;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
</style>
