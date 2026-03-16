<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NTag, NButton, NEllipsis } from 'naive-ui'
import { BookmarkOutline, CopyOutline } from '@vicons/ionicons5'
import DynastyBadge from './DynastyBadge.vue'

interface Props {
  id: string
  title: string
  author: string
  dynasty: string
  content?: string
  tags?: string[]
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true
})

const router = useRouter()

const excerpt = computed(() => {
  if (props.content) {
    return props.content.split('\n').slice(0, 2).join(' / ')
  }
  return ''
})

const goToDetail = () => {
  router.push(`/poem/${props.id}`)
}

const goToAuthor = (e: Event) => {
  e.stopPropagation()
  router.push(`/authors?search=${encodeURIComponent(props.author)}`)
}

const copyPoem = (e: Event) => {
  e.stopPropagation()
  const text = `${props.title}\n${props.author}〔${props.dynasty}〕\n\n${props.content || ''}`
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <NCard 
    class="poem-card" 
    hoverable 
    @click="goToDetail"
  >
    <template #header>
      <div class="poem-card-header">
        <h3 class="poem-title">
          <NEllipsis :line-clamp="1">{{ title || '无题' }}</NEllipsis>
        </h3>
        <DynastyBadge :dynasty="dynasty" size="small" />
      </div>
    </template>

    <div class="poem-body">
      <p v-if="excerpt" class="poem-excerpt">
        <NEllipsis :line-clamp="2" :line-height="22">{{ excerpt }}</NEllipsis>
      </p>
      
      <div class="poem-meta">
        <span class="author-name" @click="goToAuthor">{{ author }}</span>
      </div>

      <div v-if="tags?.length" class="poem-tags">
        <NTag 
          v-for="tag in tags.slice(0, 3)" 
          :key="tag" 
          size="small" 
          :bordered="false"
          type="info"
        >
          {{ tag }}
        </NTag>
        <NTag v-if="tags.length > 3" size="small" :bordered="false" type="default">
          +{{ tags.length - 3 }}
        </NTag>
      </div>
    </div>

    <template v-if="showActions" #action>
      <NButton quaternary size="small" @click="goToAuthor">
        <template #icon>
          <BookmarkOutline />
        </template>
        作者
      </NButton>
      <NButton quaternary size="small" @click="copyPoem">
        <template #icon>
          <CopyOutline />
        </template>
        复制
      </NButton>
    </template>
  </NCard>
</template>

<style scoped>
.poem-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.poem-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-seal, #8b2635);
}

.poem-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.poem-title {
  margin: 0;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  flex: 1;
  min-width: 0;
}

.poem-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.poem-excerpt {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink-light, #666);
  line-height: 22px;
}

.poem-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-size: 14px;
  color: var(--color-seal, #8b2635);
  cursor: pointer;
  transition: opacity 0.2s;
}

.author-name:hover {
  opacity: 0.7;
  text-decoration: underline;
}

.poem-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

:deep(.n-card__action) {
  padding: 8px 12px;
}
</style>
