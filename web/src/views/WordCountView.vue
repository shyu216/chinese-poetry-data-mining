<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NCard, NSpin, NEmpty, NInput, NSpace, NTag,
  NButton, NPagination, NGrid, NGridItem, NProgress, NSelect
} from 'naive-ui'
import {
  TextOutline,
  LibraryOutline, StarOutline, ResizeOutline, GitNetworkOutline
} from '@vicons/ionicons5'
import { useWordcountV2 } from '@/composables/useWordcountV2'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { useWordcountMetadata, WORDCOUNT_STORAGE } from '@/composables/useMetadataLoader'
import { useWordSimilarityMetadata, WORD_SIMILARITY_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata, getCache, getChunkedCache } from '@/composables/useCacheV2'
import { useWordSearch } from '@/search'
import type { WordCountItem } from '@/composables/types'
import PageHeader from '@/components/PageHeader.vue'
import FilterSection from '@/components/FilterSection.vue'
import StatsCard from '@/components/StatsCard.vue'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'
import WordCloud from '@/components/WordCloud.vue'
import { SearchContainer } from '@/components/search'

const wordcountV2 = useWordcountV2()
const wordSimV2 = useWordSimilarityV2()
const router = useRouter()
const route = useRoute()
const wordcountMeta = useWordcountMetadata()
const wordSimMeta = useWordSimilarityMetadata()
const chunkLoader = useChunkLoader()
const wordSimChunkLoader = useChunkLoader()

// 新的词汇搜索模块
const { search: searchWords, isReady: wordSearchReady } = useWordSearch()
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: '' })

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const loadedWords = ref<WordCountItem[]>([])
const hasMoreChunks = ref(true)
const isInitializing = ref(true)
const cachedChunksCount = ref(0)
const totalWords = ref(0)
const totalChunks = ref(0)
const lengthFilter = ref<string | null>(null)

// 词境模块数据
interface WordSimItem {
  word: string
  wordId: number
  frequency: number
  loaded: boolean
  similarWords: Array<{ word: string; similarity: number }>
}

const loadedWordSimWords = ref<WordSimItem[]>([])
const wordSimCachedChunksCount = ref(0)
const wordSimTotalChunks = ref(0)
const isWordSimInitializing = ref(true)
const wordSimHasMoreChunks = ref(true)

const lengthOptions = [
  { label: '全部长度', value: '' },
  { label: '单字', value: '1' },
  { label: '二字', value: '2' },
  { label: '三字', value: '3' },
  { label: '四字', value: '4' },
  { label: '五字及以上', value: '5+' }
]

// 搜索结果
const searchResults = ref<WordCountItem[]>([])
const searchTotal = ref(0)

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

// 使用 WordSearch 搜索
const performSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query || !wordSearchReady.value) {
    searchResults.value = []
    searchTotal.value = 0
    return
  }

  isSearching.value = true
  try {
    const result = await searchWords(query, {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
    searchResults.value = result.items
    searchTotal.value = result.total
    searchStats.value = { queryTime: result.queryTime, source: result.source }
  } finally {
    isSearching.value = false
  }
}

const displayWords = computed(() => {
  const query = searchQuery.value.trim()
  if (query && wordSearchReady.value) {
    return searchResults.value
  }
  return filteredWords.value
})

// 显示的总数（用于搜索统计）
const displayTotal = computed(() => {
  const query = searchQuery.value.trim()
  if (query && wordSearchReady.value) {
    return searchTotal.value
  }
  return filteredWords.value.length
})

const totalPages = computed(() => {
  const query = searchQuery.value.trim()
  if (query && wordSearchReady.value) {
    return Math.ceil(searchTotal.value / pageSize.value)
  }
  return Math.ceil(displayWords.value.length / pageSize.value)
})

const paginatedWords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return displayWords.value.slice(start, end)
})

// 合并后的统计计算属性
const globalTotalWords = computed(() => wordcountV2.totalWords.value || 0)
const globalTotalChunks = computed(() => wordcountV2.totalChunks.value || 0)

const topWord = computed(() => {
  if (loadedWords.value.length === 0) return '-'
  return loadedWords.value[0]?.word || '-'
})

const topCount = computed(() => {
  if (loadedWords.value.length === 0) return 0
  return loadedWords.value[0]?.count || 0
})

const avgWordLength = computed(() => {
  if (loadedWords.value.length === 0) return '-'
  const totalWeightedLength = loadedWords.value.reduce(
    (sum, w) => sum + w.word.length * w.count, 0
  )
  const totalCount = loadedWords.value.reduce(
    (sum, w) => sum + w.count, 0
  )
  return totalCount > 0 ? (totalWeightedLength / totalCount).toFixed(2) : '0'
})

// 词境统计
const wordSimTotalWords = computed(() => wordSimV2.vocabSize.value || 0)

const loadedChunksCount = computed(() => cachedChunksCount.value + chunkLoader.loadedCount.value)
const hasMoreToLoad = computed(() => loadedChunksCount.value < totalChunks.value)

const loadingHint = computed(() => {
  const count = loadedWords.value.length
  if (count === 0) return '🚀 正在连接...'
  return `📊 已加载 ${count.toLocaleString()} 个词汇...`
})

const loadCachedChunks = async (): Promise<number[]> => {
  const meta = await getMetadata(WORDCOUNT_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  cachedChunksCount.value = loadedChunkIds.length

  if (loadedChunkIds.length === 0) {
    return []
  }

  const cachedWords: WordCountItem[] = []
  for (const chunkId of loadedChunkIds) {
    const chunkData = await getChunkedCache<WordCountItem[]>(WORDCOUNT_STORAGE, chunkId)
    if (chunkData) {
      cachedWords.push(...chunkData)
    }
  }

  if (cachedWords.length > 0) {
    loadedWords.value = cachedWords.sort((a, b) => a.rank - b.rank)
    totalWords.value = cachedWords.length
  }

  return loadedChunkIds
}

const loadData = async () => {
  isInitializing.value = true
  try {
    await wordcountMeta.loadMetadata()
    const totalChunksCount = globalTotalChunks.value || 0
    totalChunks.value = totalChunksCount

    const loadedChunkIds = await loadCachedChunks()

    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))

    if (unloadedChunkIds.length === 0) {
      hasMoreChunks.value = false
      return
    }

    await chunkLoader.loadChunks<WordCountItem[]>(unloadedChunkIds, wordcountV2.loadChunk, {
      chunkDelay: 100,
      onChunkLoaded: (_, words) => {
        const wordsArray = words as WordCountItem[]
        loadedWords.value.push(...wordsArray)
        loadedWords.value.sort((a, b) => a.rank - b.rank)
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

const goToKeyword = (word: string) => {
  router.push(`/keyword/${encodeURIComponent(word)}`)
}

// 词境模块加载函数
const loadWordSimCachedChunks = async (): Promise<number[]> => {
  const vocab = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')

  if (!vocab || Object.keys(vocab).length === 0) {
    return []
  }

  const meta = await getMetadata(WORD_SIMILARITY_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  wordSimCachedChunksCount.value = loadedChunkIds.length

  const vocabReverseMap = wordSimV2.getVocabReverseMap()
  for (const chunkId of loadedChunkIds) {
    const cached = await getChunkedCache<{ vocab: string[], entries: [number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }][] }>(WORD_SIMILARITY_STORAGE, chunkId)
    if (cached) {
      const entries = new Map(cached.entries)
      for (const [wordId, entry] of entries) {
        const word = vocabReverseMap.get(wordId) || ''
        loadedWordSimWords.value.push({
          word,
          wordId,
          frequency: entry.frequency,
          loaded: true,
          similarWords: entry.similarWords.slice(0, 5).map(sw => ({
            word: vocabReverseMap.get(sw.wordId) || '',
            similarity: sw.similarity
          }))
        })
      }
    }
  }

  return loadedChunkIds
}

const loadWordSimData = async () => {
  isWordSimInitializing.value = true
  try {
    await wordSimMeta.loadMetadata()
    const totalChunksCount = wordSimV2.totalChunks.value || 0
    wordSimTotalChunks.value = totalChunksCount

    await wordSimV2.loadVocab()

    const loadedChunkIds = await loadWordSimCachedChunks()

    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))

    if (unloadedChunkIds.length === 0) {
      wordSimHasMoreChunks.value = false
      return
    }

    await wordSimChunkLoader.loadChunks(unloadedChunkIds, wordSimV2.loadChunk, {
      chunkDelay: 100,
      onChunkLoaded: (_, chunk: any) => {
        const vocabReverseMap = wordSimV2.getVocabReverseMap()
        const entries = chunk.entries as Map<number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }>

        for (const [wordId, entry] of entries) {
          const existingWord = loadedWordSimWords.value.find(w => w.wordId === wordId)
          if (!existingWord) {
            const word = vocabReverseMap.get(wordId) || ''
            loadedWordSimWords.value.push({
              word,
              wordId,
              frequency: entry.frequency,
              loaded: true,
              similarWords: entry.similarWords.slice(0, 5).map(sw => ({
                word: vocabReverseMap.get(sw.wordId) || '',
                similarity: sw.similarity
              }))
            })
          } else {
            const word = vocabReverseMap.get(wordId) || existingWord.word
            loadedWordSimWords.value = loadedWordSimWords.value.map(w =>
              w.wordId === wordId
                ? {
                    ...w,
                    word,
                    frequency: entry.frequency,
                    loaded: true,
                    similarWords: entry.similarWords.slice(0, 5).map(sw => ({
                      word: vocabReverseMap.get(sw.wordId) || '',
                      similarity: sw.similarity
                    }))
                  }
                : w
            )
          }
        }
      },
      onComplete: () => {
        wordSimHasMoreChunks.value = false
      }
    })
  } finally {
    isWordSimInitializing.value = false
  }
}

// 词境模块计算属性
const wordSimLoadedChunksCount = computed(() => wordSimCachedChunksCount.value + wordSimChunkLoader.loadedCount.value)
const wordSimHasMoreToLoad = computed(() => wordSimLoadedChunksCount.value < wordSimTotalChunks.value)

const wordSimLoadingHint = computed(() => {
  const count = loadedWordSimWords.value.length
  if (count === 0) return '🚀 正在连接...'
  return `🔗 已加载 ${count.toLocaleString()} 个词汇...`
})

// 获取词的词境信息
const getWordSimInfo = (word: string): { status: 'loading' | 'no-data' | 'has-data', similarWords: Array<{ word: string; similarity: number }> } => {
  const simWord = loadedWordSimWords.value.find(w => w.word === word)
  if (!simWord) {
    // 如果词境数据还在加载中，返回loading状态
    if (wordSimChunkLoader.isLoading.value || isWordSimInitializing.value) {
      return { status: 'loading', similarWords: [] }
    }
    return { status: 'no-data', similarWords: [] }
  }
  if (simWord.similarWords.length === 0) {
    return { status: 'no-data', similarWords: [] }
  }
  return { status: 'has-data', similarWords: simWord.similarWords }
}

const getSimilarityColor = (similarity: number) => {
  if (similarity >= 0.9) return 'success'
  if (similarity >= 0.7) return 'warning'
  if (similarity >= 0.5) return 'info'
  return 'default'
}

const getSimilarityPercent = (similarity: number) => {
  return Math.round(similarity * 100)
}

const isLoading = computed(() => (chunkLoader.isLoading.value && loadedWords.value.length === 0))

const wordcloudWords = computed(() => {
  let result = loadedWords.value

  if (lengthFilter.value) {
    if (lengthFilter.value === '5+') {
      result = result.filter(w => w.word.length >= 5)
    } else {
      const len = parseInt(lengthFilter.value)
      result = result.filter(w => w.word.length === len)
    }
  }

  return result.slice(0, 100)
})

const isWordCloudReady = computed(() => loadedWords.value.length > 0 && !chunkLoader.isLoading.value)

const handleWordCloudClick = (word: WordCountItem) => {
  goToKeyword(word.word)
}

onMounted(async () => {
  await loadData()

  // 同时加载词境数据
  loadWordSimData()

  const queryWord = route.query.word as string
  if (queryWord) {
    searchQuery.value = queryWord
    await performSearch()
  }
})

watch(searchQuery, () => {
  currentPage.value = 1
  performSearch()
})

watch(lengthFilter, () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="wordcount-view">
    <PageHeader
      title="词频排行榜"
      :subtitle="`收录 ${globalTotalWords.toLocaleString()} 个高频词汇，按使用频率排序`"
      :icon="TextOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard
          label="总收录词"
          :value="globalTotalWords.toLocaleString()"
          :prefix-icon="LibraryOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="高频词"
          :value="wordSimTotalWords.toLocaleString()"
          :prefix-icon="GitNetworkOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="最高频率"
          :value="topCount.toLocaleString()"
          suffix="次"
          :prefix-icon="StarOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="平均长度"
          :value="avgWordLength"
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
      title="加载词频数据"
      :hint="loadingHint"
      :stats="[
        { label: '已加载词汇', value: loadedWords.length.toLocaleString() + ' 个' },
        { label: '缓存分块', value: cachedChunksCount.toLocaleString() + ' 个' }
      ]"
      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
    />

    <ChunkLoaderStatus
      v-if="wordSimChunkLoader.isLoading.value || wordSimCachedChunksCount > 0"
      :is-loading="wordSimChunkLoader.isLoading.value"
      :is-paused="wordSimChunkLoader.isPaused.value"
      :progress="Math.round((wordSimLoadedChunksCount / (wordSimTotalChunks || 1)) * 100)"
      :loaded-count="wordSimLoadedChunksCount"
      :total-count="wordSimTotalChunks"
      title="加载词境数据"
      :hint="wordSimLoadingHint"
      :stats="[
        { label: '已加载词汇', value: loadedWordSimWords.length.toLocaleString() + ' 个' },
        { label: '缓存分块', value: wordSimCachedChunksCount.toLocaleString() + ' 个' }
      ]"
      @pause="wordSimChunkLoader.pause"
      @resume="wordSimChunkLoader.resume"
    />

    <WordCloud
      v-if="isWordCloudReady"
      :words="wordcloudWords"
      :max-words="80"
      :width="700"
      :height="350"
      :loading="chunkLoader.isLoading.value"
      @click="handleWordCloudClick"
    />

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索词汇..."
      :total="displayTotal"
      :query-time="searchStats.queryTime"
      :source="searchStats.source as any"
      :loading="isSearching"
      @search="handleSearch"
      @clear="clearFilters"
    >
      <template #filters>
        <NSelect
          v-model:value="lengthFilter"
          :options="lengthOptions"
          placeholder="按长度筛选"
          style="width: 130px"
          size="medium"
          clearable
        />
      </template>
    </SearchContainer>

    <NSpin :show="isInitializing && loadedWords.length === 0" size="large">
      <NEmpty
        v-if="!isInitializing && loadedWords.length === 0"
        :description="hasMoreToLoad ? '加载更多数据可能会有结果' : '暂无词频数据'"
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

      <div v-else class="wordcount-container">
        <div class="words-grid">
          <div
            v-for="word in paginatedWords"
            :key="word.rank"
            class="word-card"
            @click="goToKeyword(word.word)"
          >
            <div class="rank-badge" :class="{ 'top-ten': word.rank <= 10 }">
              {{ word.rank }}
            </div>
            <div class="word-info">
              <h3 class="word-text">{{ word.word }}</h3>
              <div class="word-stats">
                <NTag type="primary" size="small">
                  {{ word.count.toLocaleString() }} 次
                </NTag>
              </div>
              <!-- 词境信息 -->
              <div class="word-similarity">
                <template v-if="getWordSimInfo(word.word).status === 'loading'">
                  <NTag type="default" size="small" class="sim-tag loading-tag">
                    解析中...
                  </NTag>
                </template>
                <template v-else-if="getWordSimInfo(word.word).status === 'has-data'">
                  <div class="similar-words">
                    <NTag
                      v-for="sw in getWordSimInfo(word.word).similarWords.slice(0, 3)"
                      :key="sw.word"
                      :type="getSimilarityColor(sw.similarity)"
                      size="small"
                      class="sim-tag"
                    >
                      {{ sw.word }}
                    </NTag>
                  </div>
                </template>
                <template v-else>
                  <!-- no-data: 不显示任何内容 -->
                </template>
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
.wordcount-view {
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

.wordcount-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.word-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
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
  font-size: 16px;
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
}

.word-similarity {
  margin-top: 6px;
  min-height: 24px;
}

.similar-words {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.sim-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.sim-text {
  margin-left: 4px;
}

.word-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
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
  .wordcount-view {
    padding: 16px;
  }

  .words-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
</style>
