<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useKeywordIndex } from '@/composables/useKeywordIndex'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useWordcountV2 } from '@/composables/useWordcountV2'
import type { PoemSummary } from '@/composables/types'
import {
  NCard, NSpin, NEmpty, NTag, NButton, NSpace,
  NPageHeader, NGrid, NGridItem, NStatistic, NBackTop
} from 'naive-ui'
import {
  ArrowBackOutline, SearchOutline, BookOutline,
  TextOutline, TrendingUpOutline, ListOutline
} from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()
const keywordIndex = useKeywordIndex()
const poemsV2 = usePoemsV2()
const wordcountV2 = useWordcountV2()

const keyword = computed(() => route.params.word as string)
const poemIds = ref<string[]>([])
const poems = ref<PoemSummary[]>([])
const loading = ref(true)
const wordRank = ref<number | null>(null)
const wordCount = ref<number | null>(null)

const totalPoems = computed(() => poemsV2.totalPoems.value)

const dynastyStats = computed(() => {
  const stats: Record<string, number> = {}
  poems.value.forEach(p => {
    const d = p.dynasty || '未知'
    stats[d] = (stats[d] || 0) + 1
  })
  return Object.entries(stats)
    .map(([dynasty, count]) => ({ dynasty, count }))
    .sort((a, b) => b.count - a.count)
})

const genreStats = computed(() => {
  const stats: Record<string, number> = {}
  poems.value.forEach(p => {
    const g = p.genre || '未知'
    stats[g] = (stats[g] || 0) + 1
  })
  return Object.entries(stats)
    .map(([genre, count]) => ({ genre, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const loadData = async () => {
  loading.value = true
  try {
    poemIds.value = await keywordIndex.getKeywordPoemIds(keyword.value)
    
    const poemSummaries: PoemSummary[] = []
    for (const id of poemIds.value) {
      const poem = await poemsV2.getPoemById(id)
      if (poem) {
        poemSummaries.push({
          id: poem.id,
          title: poem.title,
          author: poem.author,
          dynasty: poem.dynasty,
          genre: poem.genre
        })
      }
    }
    poems.value = poemSummaries
    
    const allWords = await wordcountV2.getTopWords(10000)
    const foundWord = allWords.find(w => w.word === keyword.value)
    if (foundWord) {
      wordRank.value = foundWord.rank
      wordCount.value = foundWord.count
    }
  } catch (e) {
    console.error('Failed to load keyword data:', e)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const goToPoem = (poemId: string) => {
  router.push(`/poems/${poemId}`)
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
        <NCard class="stat-card">
          <NStatistic label="出现频次">
            <template #prefix>
              <TrendingUpOutline />
            </template>
            <span class="stat-value">{{ wordCount !== null ? wordCount.toLocaleString() : '-' }}</span>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="词频排名">
            <template #prefix>
              <TextOutline />
            </template>
            <span class="stat-value">{{ wordRank !== null ? `#${wordRank.toLocaleString()}` : '-' }}</span>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="收录诗词">
            <template #prefix>
              <BookOutline />
            </template>
            <span class="stat-value">{{ poemIds.length.toLocaleString() }} / {{ totalPoems.toLocaleString() }}</span>
          </NStatistic>
        </NCard>
      </NGridItem>
      <NGridItem>
        <NCard class="stat-card">
          <NStatistic label="朝代分布">
            <template #prefix>
              <ListOutline />
            </template>
            <span class="stat-value">{{ dynastyStats.length }} 个</span>
          </NStatistic>
        </NCard>
      </NGridItem>
    </NGrid>

    <NSpin :show="loading" size="large">
      <NEmpty v-if="!loading && poems.length === 0" :description="`未找到包含「${keyword}」的诗词`">
        <template #extra>
          <NButton @click="goToPoems">返回诗词列表</NButton>
        </template>
      </NEmpty>

      <template v-else>
        <NCard v-if="dynastyStats.length > 0" title="朝代分布" class="stats-card">
          <div class="stats-bars">
            <div v-for="stat in dynastyStats" :key="stat.dynasty" class="stat-bar-item">
              <span class="stat-label" :style="{ color: getDynastyColor(stat.dynasty) }">
                {{ stat.dynasty }}
              </span>
              <div class="stat-bar-container">
                <div 
                  class="stat-bar" 
                  :style="{ 
                    width: `${(stat.count / poemIds.length) * 100}%`,
                    background: getDynastyColor(stat.dynasty)
                  }"
                ></div>
              </div>
              <span class="stat-count">{{ stat.count }}</span>
            </div>
          </div>
        </NCard>

        <NCard v-if="genreStats.length > 0" title="体裁分布" class="stats-card">
          <div class="tags-list">
            <NTag v-for="stat in genreStats" :key="stat.genre" size="medium">
              {{ stat.genre }} ({{ stat.count }})
            </NTag>
          </div>
        </NCard>

        <NCard title="包含该关键词的诗词" class="poems-card">
          <div class="poems-list">
            <div
              v-for="poem in poems"
              :key="poem.id"
              class="poem-item"
              @click="goToPoem(poem.id)"
            >
              <div class="poem-info">
                <h3 class="poem-title">{{ poem.title || '无题' }}</h3>
                <div class="poem-meta">
                  <span 
                    class="dynasty-badge" 
                    :style="{ color: getDynastyColor(poem.dynasty) }"
                  >
                    {{ poem.dynasty || '未知' }}
                  </span>
                  <span class="author-link" @click.stop="goToAuthor(poem.author)">
                    {{ poem.author }}
                  </span>
                </div>
              </div>
            </div>
          </div>
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

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
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

.poems-list {
  display: flex;
  flex-direction: column;
}

.poem-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.poem-item:last-child {
  border-bottom: none;
}

.poem-item:hover {
  background: rgba(139, 38, 53, 0.04);
}

.poem-info {
  flex: 1;
  min-width: 0;
}

.poem-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.poem-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.dynasty-badge {
  font-weight: 500;
}

.author-link {
  color: #8b2635;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.author-link:hover {
  opacity: 0.7;
  text-decoration: underline;
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
