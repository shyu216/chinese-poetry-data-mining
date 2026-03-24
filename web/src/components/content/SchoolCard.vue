<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NTag, NIcon } from 'naive-ui'
import { PeopleOutline, BookOutline, RibbonOutline } from '@vicons/ionicons5'

interface SchoolCardProps {
  id: string
  name: string
  size: number
  representativeAuthors: string[]
  avgPoems: number
  topWords: string[]
  poemTypes: { type: string; count: number }[]
  color?: string
}

const props = withDefaults(defineProps<SchoolCardProps>(), {
  color: '#8B2635'
})

const router = useRouter()

const goToDetail = () => {
  router.push(`/authors/clusters/${props.id}`)
}

const formatNumber = (num: number): string => {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

const displayAuthors = computed(() => {
  return props.representativeAuthors.slice(0, 3)
})

const moreAuthors = computed(() => {
  return Math.max(0, props.representativeAuthors.length - 3)
})

const displayWords = computed(() => {
  return props.topWords.slice(0, 6)
})

const displayTypes = computed(() => {
  return props.poemTypes.slice(0, 3)
})
</script>

<template>
  <div class="school-card-wrapper" @click="goToDetail">
    <NCard class="school-card" hoverable>
      <!-- 流派标识 -->
      <div class="school-badge" :style="{ background: color }">
        <NIcon :size="16" color="#fff">
          <RibbonOutline />
        </NIcon>
      </div>

      <template #header>
        <div class="card-header">
          <h3 class="school-name">{{ name }}</h3>
          <div class="school-meta">
            <span class="meta-item">
              <NIcon :size="14"><PeopleOutline /></NIcon>
              {{ formatNumber(size) }}人
            </span>
            <span class="meta-item">
              <NIcon :size="14"><BookOutline /></NIcon>
              平均{{ Math.round(avgPoems) }}首诗
            </span>
          </div>
        </div>
      </template>

      <!-- 代表诗人 -->
      <div class="authors-section">
        <div class="section-label">代表诗人</div>
        <div class="authors-list">
          <span 
            v-for="(author, i) in displayAuthors" 
            :key="i"
            class="author-item"
          >
            {{ author }}
          </span>
          <span v-if="moreAuthors > 0" class="more-authors">
            +{{ moreAuthors }}
          </span>
        </div>
      </div>

      <!-- 特色词汇 -->
      <div class="words-section">
        <div class="section-label">特色词汇</div>
        <div class="words-cloud">
          <NTag
            v-for="(word, i) in displayWords"
            :key="i"
            size="small"
            :bordered="false"
            type="info"
          >
            {{ word }}
          </NTag>
        </div>
      </div>

      <!-- 主要诗体 -->
      <div class="types-section">
        <div class="section-label">主要诗体</div>
        <div class="types-list">
          <span
            v-for="(item, i) in displayTypes"
            :key="i"
            class="type-item"
          >
            {{ item.type }} ({{ formatNumber(item.count) }})
          </span>
        </div>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.school-card-wrapper {
  cursor: pointer;
  transition: transform 0.3s ease;
}

.school-card-wrapper:hover {
  transform: translateY(-4px);
}

.school-card {
  position: relative;
  height: 100%;
}

.school-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1;
}

.card-header {
  padding-right: 24px;
}

.school-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
}

.school-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-ink-light);
}

.authors-section,
.words-section,
.types-section {
  margin-top: 16px;
}

.section-label {
  font-size: 12px;
  color: var(--color-ink-light);
  margin-bottom: 8px;
  font-weight: 500;
}

.authors-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.author-item {
  font-size: 14px;
  color: var(--color-ink);
  font-weight: 500;
}

.more-authors {
  font-size: 13px;
  color: var(--color-accent);
}

.words-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.types-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.type-item {
  font-size: 13px;
  color: var(--color-ink-light);
  background: var(--color-bg-paper);
  padding: 4px 8px;
  border-radius: 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .school-name {
    font-size: 16px;
  }

  .school-meta {
    gap: 12px;
  }

  .meta-item {
    font-size: 12px;
  }
}
</style>
