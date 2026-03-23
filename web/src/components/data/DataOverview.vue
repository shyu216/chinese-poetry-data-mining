<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NCard, NGrid, NGridItem, NStatistic, NButton,
  NSpace, NTag, NProgress, NEmpty, NSpin,
  NNumberAnimation, NDivider
} from 'naive-ui'
import {
  CloudDownloadOutline, TrashOutline, SpeedometerOutline
} from '@vicons/ionicons5'

import { usePoemsMetadata, useAuthorsMetadata, useWordcountMetadata, usePoemIndexManifest, useWordSimilarityMetadata, POEMS_STORAGE, AUTHORS_STORAGE, WORDCOUNT_STORAGE, POEM_INDEX_STORAGE, WORD_SIMILARITY_STORAGE } from '@/composables/useMetadataLoader'
import { useKeywordIndex } from '@/composables/useKeywordIndex'
import { getMetadata, getCache, clearStorage, getAllStorageStats, getBrowserStorageInfo, type StorageStats, type BrowserStorageInfo } from '@/composables/useCacheV2'
import type { PoemsIndex, AuthorsIndex, WordCountMeta } from '@/composables/types'
import DataItemCard from './DataItemCard.vue'

const emit = defineEmits<{
  (e: 'switch-tab', tab: string): void
  (e: 'refresh'): void
}>()

const props = defineProps<{
  isLoadingStats?: boolean
}>()

const poemsMeta = usePoemsMetadata()
const authorsMeta = useAuthorsMetadata()
const wordcountMeta = useWordcountMetadata()
const poemIndexMeta = usePoemIndexManifest()
const wordSimMeta = useWordSimilarityMetadata()

const poemsIndexData = ref<PoemsIndex | null>(null)
const authorsIndexData = ref<AuthorsIndex | null>(null)
const wordcountIndexData = ref<WordCountMeta | null>(null)

const poemStats = ref({
  cachedChunkIds: [] as number[],
  totalChunks: 0,
  loaded: false
})

const authorStats = ref({
  cachedChunkIds: [] as number[],
  totalChunks: 0,
  loaded: false
})

const wordcountStats = ref({
  cachedChunkIds: [] as number[],
  totalChunks: 0,
  loaded: false
})

const searchIndexStats = ref({
  cachedPrefixes: 0,
  totalPrefixes: 0,
  loaded: false
})

const wordSimStats = ref({
  vocabCached: false,
  vocabSize: 0,
  cachedChunks: 0,
  totalChunks: 0
})

const keywordIndexStats = ref({
  cachedChunks: 0,
  totalChunks: 0,
  loaded: false
})

const keywordIndex = useKeywordIndex()

const loadStats = async () => {
  const poemsMetaData = await poemsMeta.loadMetadata()
  poemsIndexData.value = poemsMetaData
  poemStats.value.totalChunks = poemsMetaData?.metadata?.chunks || 0

  const poemMeta = await getMetadata(POEMS_STORAGE)
  if (poemMeta) {
    poemStats.value.cachedChunkIds = poemMeta.loadedChunkIds || []
    poemStats.value.loaded = true
  }

  const authorsMetaData = await authorsMeta.loadMetadata()
  authorsIndexData.value = authorsMetaData
  authorStats.value.totalChunks = authorsMetaData?.total || 0

  const authorMeta = await getMetadata(AUTHORS_STORAGE)
  if (authorMeta) {
    authorStats.value.cachedChunkIds = authorMeta.loadedChunkIds || []
    authorStats.value.loaded = true
  }

  const wordcountMetaData = await wordcountMeta.loadMetadata()
  wordcountIndexData.value = wordcountMetaData
  wordcountStats.value.totalChunks = wordcountMetaData?.total_chunks || 0

  const wordcountMetaStored = await getMetadata(WORDCOUNT_STORAGE)
  if (wordcountMetaStored) {
    wordcountStats.value.cachedChunkIds = wordcountMetaStored.loadedChunkIds || []
    wordcountStats.value.loaded = true
  }

  const searchIndexMetaData = await poemIndexMeta.loadMetadata()
  searchIndexStats.value.totalPrefixes = Object.keys(searchIndexMetaData?.prefixMap || {}).length

  const searchIndexPrefixes = await getCache<string[]>(POEM_INDEX_STORAGE, 'loaded-prefixes')
  if (searchIndexPrefixes) {
    searchIndexStats.value.cachedPrefixes = searchIndexPrefixes.length
    searchIndexStats.value.loaded = true
  }

  const wordSimMetaData = await wordSimMeta.loadMetadata()
  wordSimStats.value.totalChunks = wordSimMetaData?.total_chunks || 0
  wordSimStats.value.vocabSize = wordSimMetaData?.vocab_size || 0

  const wordSimVocab = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')
  if (wordSimVocab && Object.keys(wordSimVocab).length > 0) {
    wordSimStats.value.vocabCached = true
  }

  const wordSimMetaStored = await getMetadata(WORD_SIMILARITY_STORAGE)
  if (wordSimMetaStored && wordSimMetaStored.loadedChunkIds) {
    const validIds = wordSimMetaStored.loadedChunkIds.filter((id: number) => id < (wordSimMetaStored.totalChunks || 0))
    wordSimStats.value.cachedChunks = validIds.length
  }

  // 使用 computed 属性获取 keyword index 统计
  keywordIndexStats.value.totalChunks = keywordIndex.totalChunks.value
  keywordIndexStats.value.cachedChunks = keywordIndex.loadedChunkIds.value.length
  keywordIndexStats.value.loaded = keywordIndexStats.value.cachedChunks > 0

  console.log('[DataOverview] wordSimStats:', {
    totalChunks: wordSimStats.value.totalChunks,
    vocabSize: wordSimStats.value.vocabSize,
    vocabCached: wordSimStats.value.vocabCached,
    cachedChunks: wordSimStats.value.cachedChunks
  })
  console.log('[DataOverview] searchIndexStats:', {
    totalPrefixes: searchIndexStats.value.totalPrefixes,
    cachedPrefixes: searchIndexStats.value.cachedPrefixes,
    loaded: searchIndexStats.value.loaded
  })
}

const handleClearCache = async () => {
  await clearStorage(POEMS_STORAGE)
  await clearStorage(AUTHORS_STORAGE)
  await clearStorage(WORDCOUNT_STORAGE)
  await clearStorage(POEM_INDEX_STORAGE)
  await clearStorage(WORD_SIMILARITY_STORAGE)
  await clearStorage(keywordIndex.storageName)

  poemStats.value.cachedChunkIds = []
  authorStats.value.cachedChunkIds = []
  wordcountStats.value.cachedChunkIds = []
  searchIndexStats.value.cachedPrefixes = 0
  wordSimStats.value.cachedChunks = 0
  wordSimStats.value.vocabCached = false
  keywordIndexStats.value.cachedChunks = 0
  keywordIndexStats.value.loaded = false

  emit('refresh')
}

const poemChunkBars = computed(() => {
  if (!poemsIndexData.value?.chunks) return []
  const cachedSet = new Set(poemStats.value.cachedChunkIds)
  return poemsIndexData.value.chunks.map(chunk => ({
    id: chunk.id,
    count: chunk.count,
    cached: cachedSet.has(chunk.id)
  }))
})

const authorChunkBars = computed(() => {
  if (!authorsIndexData.value?.chunks) return []
  const cachedSet = new Set(authorStats.value.cachedChunkIds)
  return authorsIndexData.value.chunks.map(chunk => ({
    id: chunk.index,
    count: chunk.authorCount,
    cached: cachedSet.has(chunk.index)
  }))
})

const wordcountChunkBars = computed(() => {
  if (!wordcountIndexData.value?.chunks) return []
  const cachedSet = new Set(wordcountStats.value.cachedChunkIds)
  return wordcountIndexData.value.chunks.map(chunk => ({
    id: chunk.index,
    count: chunk.count,
    cached: cachedSet.has(chunk.index)
  }))
})

const maxPoemCount = computed(() => {
  if (!poemChunkBars.value.length) return 0
  return Math.max(...poemChunkBars.value.map(c => c.count))
})

const maxAuthorCount = computed(() => {
  if (!authorChunkBars.value.length) return 0
  return Math.max(...authorChunkBars.value.map(c => c.count))
})

const maxWordcountCount = computed(() => {
  if (!wordcountChunkBars.value.length) return 0
  return Math.max(...wordcountChunkBars.value.map(c => c.count))
})

const wordSimChunkBars = computed(() => {
  const total = wordSimStats.value.totalChunks
  if (total === 0) return []
  const cachedSet = new Set<number>()
  for (let i = 0; i < wordSimStats.value.cachedChunks; i++) {
    cachedSet.add(i)
  }
  return Array.from({ length: total }, (_, i) => ({
    id: i,
    count: Math.ceil(wordSimStats.value.vocabSize / total),
    cached: cachedSet.has(i)
  }))
})

const searchIndexChunkBars = computed(() => {
  const total = searchIndexStats.value.totalPrefixes
  if (total === 0) return []
  const cached = searchIndexStats.value.cachedPrefixes
  const cachedRatio = total > 0 ? cached / total : 0
  return Array.from({ length: Math.min(total, 50) }, (_, i) => ({
    id: i,
    count: Math.ceil(total / 50),
    cached: i / 50 < cachedRatio
  }))
})

const keywordIndexChunkBars = computed(() => {
  const total = keywordIndexStats.value.totalChunks
  if (total === 0) return []
  const cached = keywordIndexStats.value.cachedChunks
  const cachedRatio = total > 0 ? cached / total : 0
  return Array.from({ length: Math.min(total, 50) }, (_, i) => ({
    id: i,
    count: Math.ceil(total / 50),
    cached: i / 50 < cachedRatio
  }))
})

const maxWordSimCount = computed(() => {
  if (!wordSimChunkBars.value.length) return 0
  return Math.max(...wordSimChunkBars.value.map(c => c.count))
})

const maxSearchIndexCount = computed(() => {
  if (!searchIndexChunkBars.value.length) return 0
  return Math.max(...searchIndexChunkBars.value.map(c => c.count))
})

defineExpose({
  loadStats
})
</script>

<template>
  <NSpin :show="isLoadingStats">
    <NSpace vertical size="large">
      <NGrid :cols="3" :x-gap="16" :y-gap="16">
        <NGridItem>
          <DataItemCard icon="📚" title="诗词" description="诗词数据库，包含三十万首诗词摘要数据，支持离线浏览"
            :cached-count="poemStats.cachedChunkIds.length" :total-count="poemStats.totalChunks" :bars="poemChunkBars"
            :max-count="maxPoemCount" color-class="poems" />
        </NGridItem>
        <NGridItem>
          <DataItemCard icon="👤" title="诗人" description="诗人数据库，包含多位诗人的生平与作品统计"
            :cached-count="authorStats.cachedChunkIds.length" :total-count="authorStats.totalChunks"
            :bars="authorChunkBars" :max-count="maxAuthorCount" color-class="authors" />
        </NGridItem>
        <NGridItem>
          <DataItemCard icon="📊" title="词频" description="词频统计数据，支持词频分析和词汇使用统计"
            :cached-count="wordcountStats.cachedChunkIds.length" :total-count="wordcountStats.totalChunks"
            :bars="wordcountChunkBars" :max-count="maxWordcountCount" color-class="wordcount" />
        </NGridItem>
        <NGridItem>
          <DataItemCard icon="🔗" title="词境" description="词境探索数据库，包含词汇相似度数据，支持词语关联分析"
            :cached-count="wordSimStats.cachedChunks" :total-count="wordSimStats.totalChunks" :bars="wordSimChunkBars"
            :max-count="maxWordSimCount" color-class="wordsim" />
        </NGridItem>
        <NGridItem>
          <DataItemCard icon="🔍" title="搜索索引" description="搜索索引包含诗词前缀数据，支持快速诗词搜索"
            :cached-count="searchIndexStats.cachedPrefixes" :total-count="searchIndexStats.totalPrefixes"
            :bars="searchIndexChunkBars" :max-count="maxSearchIndexCount" color-class="searchindex" />
        </NGridItem>
        <NGridItem>
          <DataItemCard icon="🔑" title="关键词索引" description="关键词-诗词映射数据，支持按关键词快速检索诗词"
            :cached-count="keywordIndexStats.cachedChunks" :total-count="keywordIndexStats.totalChunks"
            :bars="keywordIndexChunkBars" :max-count="keywordIndexStats.totalChunks" color-class="keywordindex" />
        </NGridItem>
      </NGrid>
    </NSpace>
  </NSpin>
</template>

<style scoped>
.stat-card {
  text-align: center;
}

.stat-card :deep(.n-statistic__label) {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.stat-card :deep(.n-statistic__value) {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.stat-icon {
  font-size: 20px;
  margin-right: 4px;
}

.stat-suffix {
  font-size: 13px;
  color: #999;
  font-weight: normal;
}

.chunk-dashboard-card {
  background: #fafafa;
}

.mini-chart {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e8e8e8;
}

.mini-chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.mini-chart-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.mini-chart-body {
  height: 80px;
  overflow-x: auto;
  overflow-y: hidden;
}

.mini-bars {
  display: flex;
  align-items: flex-end;
  gap: 1px;
  height: 100%;
  min-width: 100%;
}

.mini-bar {
  flex: 1;
  min-width: 2px;
  max-width: 6px;
  background: #e8e8e8;
  border-radius: 1px 1px 0 0;
  transition: all 0.2s ease;
  cursor: pointer;
}

.mini-bar.cached {
  background: #8b2635;
}

.mini-bar.author.cached {
  background: #2a7a6e;
}

.mini-bar.wordcount.cached {
  background: #d4a84b;
}

.mini-bar.wordsim.cached {
  background: #9c27b0;
}

.mini-bar.searchindex.cached {
  background: #00bcd4;
}

.mini-bar.keywordindex.cached {
  background: #ff9800;
}

.mini-bar:hover {
  opacity: 0.8;
}

.mini-chart-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  font-size: 11px;
  color: #666;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
  margin-right: 4px;
}

.legend-dot.cached {
  background: #8b2635;
}

.legend-dot.cached.author {
  background: #2a7a6e;
}

.legend-dot.cached.wordcount {
  background: #d4a84b;
}

.legend-dot.cached.wordsim {
  background: #9c27b0;
}

.legend-dot.cached.searchindex {
  background: #00bcd4;
}

.legend-dot.cached.keywordindex {
  background: #ff9800;
}

.legend-dot.uncached {
  background: #e8e8e8;
}
</style>
