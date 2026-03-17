<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  NCard, NSpin, NEmpty, NInput, NSpace, NTag,
  NButton, NGrid, NGridItem, NPagination
} from 'naive-ui'
import {
  SearchOutline, TextOutline, GitNetworkOutline,
  LibraryOutline, StarOutline, ResizeOutline
} from '@vicons/ionicons5'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { useWordSimilarityMetadata, WORD_SIMILARITY_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata, getCache } from '@/composables/useCacheV2'
import PageHeader from '@/components/PageHeader.vue'
import FilterSection from '@/components/FilterSection.vue'
import StatsCard from '@/components/StatsCard.vue'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'

interface WordItem {
  word: string
  wordId: number
  frequency: number
  loaded: boolean
  similarWords: Array<{ word: string; similarity: number }>
}

const wordSimV2 = useWordSimilarityV2()
const wordSimMeta = useWordSimilarityMetadata()
const chunkLoader = useChunkLoader()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const loadedWords = ref<WordItem[]>([])
const hasMoreChunks = ref(true)
const isInitializing = ref(true)
const cachedChunksCount = ref(0)
const totalWords = ref(0)
const totalChunks = ref(0)
const lengthFilter = ref<string | null>(null)
const vocabCached = ref(false)
const loadingWordDetails = ref<Set<number>>(new Set())

const lengthOptions = [
  { label: '全部长度', value: '' },
  { label: '单字', value: '1' },
  { label: '二字', value: '2' },
  { label: '三字', value: '3' },
  { label: '四字', value: '4' },
  { label: '五字及以上', value: '5+' }
]

const filteredWords = computed(() => {
  let result = loadedWords.value

  if (lengthFilter.value) {
    if (lengthFilter.value === '5+') {
      result = result.filter(w => w.word.length >= 5)
    } else {
      const len = parseInt(lengthFilter.value)
      result = result.filter(w => w.word.length === len)
    }
  }

  if (!searchQuery.value.trim()) {
    return result
  }
  const query = searchQuery.value.toLowerCase()
  return result.filter(w =>
    w.word.toLowerCase().includes(query)
  )
})

const displayWords = computed(() => filteredWords.value)

const paginatedWords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return displayWords.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(displayWords.value.length / pageSize.value))

const globalTotalWords = computed(() => wordSimV2.vocabSize.value || 0)
const globalTotalChunks = computed(() => wordSimV2.totalChunks.value || 0)

const topWord = computed(() => {
  if (loadedWords.value.length === 0) return '-'
  const sorted = [...loadedWords.value].sort((a, b) => b.frequency - a.frequency)
  return sorted[0]?.word || '-'
})

const topFrequency = computed(() => {
  if (loadedWords.value.length === 0) return 0
  const sorted = [...loadedWords.value].sort((a, b) => b.frequency - a.frequency)
  return sorted[0]?.frequency || 0
})

const longestWord = computed(() => {
  if (loadedWords.value.length === 0) return '-'
  const totalWeightedLength = loadedWords.value.reduce(
    (sum, w) => sum + w.word.length * w.frequency, 0
  )
  const totalFreq = loadedWords.value.reduce(
    (sum, w) => sum + w.frequency, 0
  )
  const avgLength = totalFreq > 0 ? (totalWeightedLength / totalFreq).toFixed(2) : '0'
  return avgLength
})

const loadedChunksCount = computed(() => cachedChunksCount.value + chunkLoader.loadedCount.value)
const hasMoreToLoad = computed(() => loadedChunksCount.value < totalChunks.value)

const loadingHint = computed(() => {
  const count = loadedWords.value.length
  if (count === 0) return '🚀 正在连接...'
  return `🔗 已加载 ${count.toLocaleString()} 个词汇...`
})

const loadCachedChunks = async (): Promise<number[]> => {
  const vocab = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')
  vocabCached.value = vocab !== null && Object.keys(vocab).length > 0

  if (!vocabCached.value) {
    return []
  }

  const meta = await getMetadata(WORD_SIMILARITY_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  cachedChunksCount.value = loadedChunkIds.length

  const vocabMap = vocab!
  const wordsArray: WordItem[] = Object.entries(vocabMap).map(([word, wordId]) => ({
    word,
    wordId: wordId as number,
    frequency: 0,
    loaded: false,
    similarWords: []
  }))

  if (wordsArray.length > 0) {
    loadedWords.value = wordsArray.sort((a, b) => a.wordId - b.wordId)
    totalWords.value = wordsArray.length
  }

  return loadedChunkIds
}

const loadData = async () => {
  isInitializing.value = true
  try {
    await wordSimMeta.loadMetadata()
    const totalChunksCount = globalTotalChunks.value || 0
    totalChunks.value = totalChunksCount

    await wordSimV2.loadVocab()
    vocabCached.value = true

    const loadedChunkIds = await loadCachedChunks()

    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))

    if (unloadedChunkIds.length === 0) {
      hasMoreChunks.value = false
      return
    }

    await chunkLoader.loadChunks(unloadedChunkIds, wordSimV2.loadChunk, {
      chunkDelay: 100,
      onChunkLoaded: (_, chunk: any) => {
        const vocab = chunk.vocab as string[]
        const entries = chunk.entries as Map<number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }>
        
        for (const [wordId, entry] of entries) {
          const wordIndex = loadedWords.value.findIndex(w => w.wordId === wordId)
          if (wordIndex !== -1) {
            const existingWord = loadedWords.value[wordIndex]
            loadedWords.value[wordIndex] = {
              word: existingWord?.word || '',
              wordId: existingWord?.wordId || 0,
              frequency: entry.frequency,
              loaded: true,
              similarWords: entry.similarWords.slice(0, 5).map(sw => ({
                word: vocab[sw.wordId] || '',
                similarity: sw.similarity
              }))
            }
          }
        }
        totalWords.value = loadedWords.value.length
      },
      onComplete: () => {
        hasMoreChunks.value = false
      }
    })
  } finally {
    isInitializing.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handlePageChange = (p: number) => {
  currentPage.value = p
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const clearFilters = () => {
  searchQuery.value = ''
  lengthFilter.value = null
  currentPage.value = 1
}

const isLoading = computed(() => (chunkLoader.isLoading.value && loadedWords.value.length === 0))

const getSimilarityColor = (similarity: number) => {
  if (similarity >= 0.9) return 'success'
  if (similarity >= 0.7) return 'warning'
  if (similarity >= 0.5) return 'info'
  return 'default'
}

const getSimilarityPercent = (similarity: number) => {
  return Math.round(similarity * 100)
}

onMounted(() => {
  loadData()
})

watch(searchQuery, () => {
  currentPage.value = 1
})

watch(lengthFilter, () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="wordsim-view">
    <PageHeader
      title="词境探索"
      :subtitle="`收录 ${globalTotalWords.toLocaleString()} 个词汇，探索词语间的相似关系`"
      :icon="GitNetworkOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard
          label="总收录词汇"
          :value="globalTotalWords.toLocaleString()"
          :prefix-icon="LibraryOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="最高频词"
          :value="topWord"
          :prefix-icon="TextOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="最高词频"
          :value="topFrequency.toLocaleString()"
          suffix="次"
          :prefix-icon="StarOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="加权平均长度"
          :value="longestWord"
          :prefix-icon="ResizeOutline"
        />
      </NGridItem>
    </NGrid>

    <ChunkLoaderStatus
      v-if="chunkLoader.isLoading.value || cachedChunksCount > 0"
      :is-loading="chunkLoader.isLoading.value"
      :is-paused="chunkLoader.isPaused.value"
      :progress="Math.round((loadedChunksCount / (totalChunks || 1)) * 100)"
      :loaded-count="loadedChunksCount"
      :total-count="totalChunks"
      title="加载词境数据"
      :hint="loadingHint"
      :stats="[
        { label: '已加载词汇', value: loadedWords.length.toLocaleString() + ' 个' },
        { label: '缓存分块', value: cachedChunksCount.toLocaleString() + ' 个' }
      ]"
      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
    />

    <FilterSection class="search-section">
      <NSpace align="center" :size="12">
        <NSelect
          v-model:value="lengthFilter"
          :options="lengthOptions"
          placeholder="按长度筛选"
          style="width: 130px"
          size="medium"
          clearable
        />
        <NInput
          v-model:value="searchQuery"
          placeholder="搜索词汇..."
          style="width: 220px"
          size="medium"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <SearchOutline style="opacity: 0.5" />
          </template>
        </NInput>
        <NButton
          type="primary"
          size="medium"
          @click="handleSearch"
          :loading="isLoading"
        >
          搜索
        </NButton>
        <NButton
          v-if="searchQuery || lengthFilter"
          size="medium"
          @click="clearFilters"
        >
          清除
        </NButton>
      </NSpace>
    </FilterSection>

    <NSpin :show="isInitializing && loadedWords.length === 0" size="large">
      <NEmpty
        v-if="!isInitializing && loadedWords.length === 0"
        :description="hasMoreToLoad ? '加载更多数据可能会有结果' : '暂无词境数据'"
      >
        <template #extra>
          <NButton v-if="hasMoreToLoad" @click="clearFilters">
            清除筛选
          </NButton>
          <NButton v-else @click="clearFilters">
            清除筛选
          </NButton>
        </template>
      </NEmpty>

      <div v-else class="wordsim-container">
        <div class="words-grid">
          <div
            v-for="word in paginatedWords"
            :key="word.wordId"
            class="word-card"
          >
            <div class="rank-badge" :class="{ 'top-ten': word.loaded && word.frequency > 0 }">
              {{ word.wordId }}
            </div>
            <div class="word-info">
              <h3 class="word-text">{{ word.word }}</h3>
              <div class="word-stats">
                <NTag v-if="word.loaded" type="primary" size="small">
                  {{ word.frequency.toLocaleString() }} 次
                </NTag>
                <NTag v-else type="default" size="small">
                  未加载
                </NTag>
              </div>
              <div v-if="word.similarWords.length > 0" class="similar-words">
                <span class="similar-label">相似词：</span>
                <NTag
                  v-for="sw in word.similarWords.slice(0, 3)"
                  :key="sw.word"
                  :type="getSimilarityColor(sw.similarity)"
                  size="small"
                >
                  {{ sw.word }} ({{ getSimilarityPercent(sw.similarity) }}%)
                </NTag>
              </div>
            </div>
          </div>
        </div>

        <div class="pagination-wrapper">
          <NPagination
            :page="currentPage"
            :page-count="totalPages"
            :page-size="pageSize"
            :page-sizes="[20, 50, 100, 200]"
            show-size-picker
            show-quick-jumper
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </div>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.wordsim-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.stats-grid {
  margin-bottom: 24px;
}

.search-section {
  margin-bottom: 24px;
}

.wordsim-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.word-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.word-card:hover {
  border-color: var(--color-seal, #8b2635);
  background: rgba(139, 38, 53, 0.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.rank-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--color-bg-elevated, #f5f5f5);
  color: var(--color-ink, #2c3e50);
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.rank-badge.top-ten {
  background: linear-gradient(135deg, #8b2635 0%, #a83246 100%);
  color: #fff;
}

.word-info {
  flex: 1;
  min-width: 0;
}

.word-text {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  line-height: 1.4;
}

.word-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.similar-words {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.similar-label {
  font-size: 12px;
  color: var(--color-ink-light, #6b7280);
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
}

@media (max-width: 768px) {
  .wordsim-view {
    padding: 16px;
  }

  .words-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}
</style>
