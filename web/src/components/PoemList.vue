<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NList, NListItem, NThing, NEmpty, NSpin, NButton, NIcon } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import DynastyBadge from './DynastyBadge.vue'

export interface PoemListItem {
  id: string
  title: string
  author: string
  dynasty: string
  content?: string
  tags?: string[]
  chunk_id?: number // 用于快速定位诗词详情
}

interface Props {
  poems: PoemListItem[]
  loading?: boolean
  emptyText?: string
  showAuthor?: boolean
  showDynasty?: boolean
  showContent?: boolean
  pageSize?: number
  total?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  emptyText: '暂无诗词',
  showAuthor: true,
  showDynasty: true,
  showContent: false,
  pageSize: 20,
  total: 0
})

const emit = defineEmits<{
  loadMore: []
}>()

const router = useRouter()

const hasMore = computed(() => {
  return props.total > props.poems.length
})

const goToPoem = (poem: PoemListItem) => {
  if (poem.chunk_id !== undefined) {
    router.push({
      path: `/poems/${poem.id}`,
      query: { chunk_id: poem.chunk_id.toString() }
    })
  } else {
    router.push(`/poems/${poem.id}`)
  }
}

const goToAuthor = (author: string, e: Event) => {
  e.stopPropagation()
  router.push(`/authors?search=${encodeURIComponent(author)}`)
}

const handleLoadMore = () => {
  emit('loadMore')
}
</script>

<template>
  <div class="poem-list">
    <NSpin :show="loading" size="medium">
      <NEmpty v-if="!loading && poems.length === 0" :description="emptyText" />
      
      <NList v-else clickable class="list-container">
        <NListItem
          v-for="poem in poems"
          :key="poem.id"
          class="poem-item"
          @click="goToPoem(poem)"
        >
          <NThing>
            <template #header>
              <div class="poem-header">
                <span class="poem-title">{{ poem.title || '无题' }}</span>
                <DynastyBadge v-if="showDynasty" :dynasty="poem.dynasty" size="small" />
              </div>
            </template>

            <template #header-extra v-if="showAuthor">
              <span class="poem-author" @click="goToAuthor(poem.author, $event)">
                {{ poem.author }}
              </span>
            </template>

            <template #description v-if="showContent && poem.content">
              <p class="poem-excerpt">{{ poem.content.split('\n').slice(0, 2).join(' / ') }}</p>
            </template>

            <template #footer v-if="poem.tags?.length">
              <div class="poem-tags">
                <span 
                  v-for="tag in poem.tags.slice(0, 3)" 
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
.poem-list {
  width: 100%;
}

.list-container {
  background: transparent;
}

.poem-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.poem-item:hover {
  border-color: var(--color-seal, #8b2635);
  background: rgba(139, 38, 53, 0.02);
}

.poem-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.poem-title {
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.poem-author {
  font-size: 14px;
  color: var(--color-seal, #8b2635);
  cursor: pointer;
  transition: opacity 0.2s;
}

.poem-author:hover {
  opacity: 0.7;
  text-decoration: underline;
}

.poem-excerpt {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink-light, #666);
  line-height: 1.6;
}

.poem-tags {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.tag {
  padding: 2px 8px;
  font-size: 12px;
  color: var(--color-seal, #8b2635);
  background: rgba(139, 38, 53, 0.08);
  border-radius: 4px;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
</style>
