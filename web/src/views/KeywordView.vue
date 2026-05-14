<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NEmpty, NButton, NPagination, NGrid, NGridItem, NSelect } from 'naive-ui'
import { TextOutline, LibraryOutline, StarOutline, ResizeOutline, FlameOutline } from '@vicons/ionicons5'
import { useWordcount } from '@/composables/useWordcount'
import { useWordSearch } from '@/search'
import type { WordCountItem } from '@/composables/types'
import { PageHeader } from '@/components/layout'
import { StatsCard, WordCloud } from '@/components/display'
import { SearchContainer } from '@/components/search'

const router = useRouter()
const route = useRoute()
const wordcount = useWordcount()
const { search: searchWords } = useWordSearch()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const currentWords = ref<WordCountItem[]>([])
const totalResults = ref(0)
const topWords = ref<WordCountItem[]>([])
const isInitializing = ref(true)
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: 'memory' })
const lengthFilter = ref<string | null>(null)
const wordCloudTitle = ref('高频词云')

const lengthOptions = [
  { label: '全部长度', value: '' },
  { label: '单字', value: '1' },
  { label: '二字', value: '2' },
  { label: '三字', value: '3' },
  { label: '四字', value: '4' },
  { label: '五字及以上', value: '5+' }
]

const displayTotal = computed(() => totalResults.value)
const totalPages = computed(() => Math.max(1, Math.ceil(displayTotal.value / pageSize.value)))
const topWord = computed(() => topWords.value[0]?.word || '-')
const topCount = computed(() => topWords.value[0]?.count || 0)
const avgWordLength = computed(() => {
  if (topWords.value.length === 0) return '-'
  const totalWeightedLength = topWords.value.reduce((sum, item) => sum + item.word.length * item.count, 0)
  const totalCount = topWords.value.reduce((sum, item) => sum + item.count, 0)
  return totalCount > 0 ? (totalWeightedLength / totalCount).toFixed(2) : '0'
})

const wordcloudWords = computed(() => {
  let list = topWords.value
  if (lengthFilter.value) {
    list = list.filter(item => {
      if (lengthFilter.value === '5+') return item.word.length >= 5
      return item.word.length === Number(lengthFilter.value)
    })
  }
  const selected = lengthOptions.find(item => item.value === (lengthFilter.value ?? ''))
  wordCloudTitle.value = `${selected?.label || '全部长度'}高频词云`
  return list.slice(0, 100)
})

async function refreshPage() {
  isSearching.value = true
  try {
    const exactLength = lengthFilter.value && lengthFilter.value !== '5+' ? Number(lengthFilter.value) : undefined
    const result = await searchWords(searchQuery.value.trim(), {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
      filters: {
        minLength: lengthFilter.value === '5+' ? 5 : exactLength,
        maxLength: lengthFilter.value === '5+' ? undefined : exactLength
      }
    })
    currentWords.value = result.items
    totalResults.value = result.total
    searchStats.value = { queryTime: result.queryTime, source: result.source }
  } finally {
    isSearching.value = false
  }
}

function clearFilters() {
  searchQuery.value = ''
  lengthFilter.value = null
  currentPage.value = 1
}

function goToKeyword(word: string) {
  router.push(`/keyword/${encodeURIComponent(word)}`)
}

function handleWordCloudClick(word: WordCountItem) {
  goToKeyword(word.word)
}

onMounted(async () => {
  try {
    await wordcount.loadMetadata()
    topWords.value = await wordcount.getTopWords(1000)
    const queryWord = route.query.word as string | undefined
    if (queryWord) {
      searchQuery.value = queryWord
    }
    await refreshPage()
  } finally {
    isInitializing.value = false
  }
})

watch(searchQuery, async () => {
  currentPage.value = 1
  await refreshPage()
})

watch(lengthFilter, async () => {
  currentPage.value = 1
  await refreshPage()
})

watch([currentPage, pageSize], async () => {
  if (isInitializing.value) return
  await refreshPage()
})
</script>

<template>
  <div class="wordcount-view">
    <PageHeader title="分词数据" :subtitle="`共收录 ${wordcount.totalWords.value.toLocaleString()} 个词汇，当前结果 ${displayTotal.toLocaleString()} 个`" :icon="TextOutline" />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem><StatsCard label="词汇总数" :value="wordcount.totalWords.value.toLocaleString()" :prefix-icon="LibraryOutline" /></NGridItem>
      <NGridItem><StatsCard label="最高频词" :value="topWord" :prefix-icon="FlameOutline" /></NGridItem>
      <NGridItem><StatsCard label="最高频率" :value="topCount.toLocaleString()" suffix="次" :prefix-icon="StarOutline" /></NGridItem>
      <NGridItem><StatsCard label="平均长度" :value="avgWordLength" :prefix-icon="ResizeOutline" /></NGridItem>
    </NGrid>

    <WordCloud v-if="wordcloudWords.length > 0" :words="wordcloudWords" :max-words="80" :width="700" :height="350" :title="wordCloudTitle" :loading="isSearching" @click="handleWordCloudClick" />

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索词汇..."
      :total="displayTotal"
      :query-time="searchStats.queryTime"
      :source="searchStats.source as any"
      :loading="isSearching"
      @clear="clearFilters"
    >
      <template #filters>
        <NSelect v-model:value="lengthFilter" :options="lengthOptions" placeholder="长度" style="width: 130px" clearable />
      </template>
    </SearchContainer>

    <NEmpty v-if="isInitializing" description="正在加载词频数据..." />
    <NEmpty v-else-if="currentWords.length === 0" description="没有匹配结果">
      <template #extra><NButton @click="clearFilters">清除筛选</NButton></template>
    </NEmpty>

    <div v-else class="wordcount-container">
      <div class="words-grid">
        <div
          v-for="row in currentWords"
          :key="`${row.rank}-${row.word}`"
          class="word-card word-card--dense"
          @click="goToKeyword(row.word)"
        >
          <div class="word-card__row word-card__row--main">
            <div class="rank-badge" :title="`排名 ${row.rank}`">{{ row.rank }}</div>
            <h3 class="word-text">{{ row.word }}</h3>
            <div class="word-card__stats">
              <span class="word-card__freq-num">{{ row.count.toLocaleString() }}</span>
              <span class="word-card__freq-unit">次</span>
              <span class="word-card__sep" aria-hidden="true">·</span>
              <span class="word-card__len">{{ row.word.length }}字</span>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-wrapper" v-if="totalPages > 1">
        <NPagination
          :page="currentPage"
          :page-count="totalPages"
          :page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          show-size-picker
          show-quick-jumper
          @update:page="currentPage = $event"
          @update:page-size="pageSize = $event"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.wordcount-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.stats-grid {
  margin-bottom: 24px;
}

.wordcount-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(168px, 1fr));
  gap: 8px;
}

.word-card {
  position: relative;
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.word-card--dense {
  padding: 8px 10px;
  min-height: 0;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e8eaed;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.word-card--dense:hover {
  background: #fafafa;
  border-color: rgba(139, 38, 53, 0.28);
  box-shadow: 0 0 0 1px rgba(139, 38, 53, 0.08);
}

.word-card__row--main {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.word-card__stats {
  flex-shrink: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 1px;
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.word-card__sep {
  margin: 0 3px;
}

.word-text {
  margin: 0;
}

.rank-badge {
  min-width: 36px;
  text-align: center;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 999px;
  background: #f3f4f6;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
}
</style>
