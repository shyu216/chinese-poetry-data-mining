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
import { getMetadata, getCache, clearStorage, getAllStorageStats, getBrowserStorageInfo, type StorageStats, type BrowserStorageInfo } from '@/composables/useCacheV2'
import type { PoemsIndex, AuthorsIndex, WordCountMeta } from '@/composables/types'

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

  const searchIndexMetaStored = await getMetadata(POEM_INDEX_STORAGE)
  if (searchIndexMetaStored) {
    searchIndexStats.value.cachedPrefixes = searchIndexMetaStored.loadedChunkIds?.length || 0
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
  if (wordSimMetaStored) {
    wordSimStats.value.cachedChunks = wordSimMetaStored.loadedChunkIds?.length || 0
  }

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

  poemStats.value.cachedChunkIds = []
  authorStats.value.cachedChunkIds = []
  wordcountStats.value.cachedChunkIds = []
  searchIndexStats.value.cachedPrefixes = 0
  wordSimStats.value.cachedChunks = 0
  wordSimStats.value.vocabCached = false

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
      <NGrid :cols="5" :x-gap="16" :y-gap="16">
        <NGridItem>
          <NCard class="stat-card">
            <NStatistic label="诗词分块">
              <template #prefix>
                <span class="stat-icon poems">📚</span>
              </template>
              <NNumberAnimation :from="0" :to="poemStats.cachedChunkIds.length" />
              <template #suffix>
                <span class="stat-suffix">/ {{ poemStats.totalChunks }}</span>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card">
            <NStatistic label="诗人分块">
              <template #prefix>
                <span class="stat-icon authors">👤</span>
              </template>
              <NNumberAnimation :from="0" :to="authorStats.cachedChunkIds.length" />
              <template #suffix>
                <span class="stat-suffix">/ {{ authorStats.totalChunks }}</span>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card">
            <NStatistic label="词频数据">
              <template #prefix>
                <span class="stat-icon wordcount">📊</span>
              </template>
              <NNumberAnimation :from="0" :to="wordcountStats.cachedChunkIds.length" />
              <template #suffix>
                <span class="stat-suffix">/ {{ wordcountStats.totalChunks }}</span>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card">
            <NStatistic label="搜索索引">
              <template #prefix>
                <span class="stat-icon search">🔍</span>
              </template>
              <NNumberAnimation :from="0" :to="searchIndexStats.cachedPrefixes" />
              <template #suffix>
                <span class="stat-suffix">/ {{ searchIndexStats.totalPrefixes }}</span>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card">
            <NStatistic label="词境数据">
              <template #prefix>
                <span class="stat-icon wordsim">🔗</span>
              </template>
              <NTag :type="wordSimStats.vocabCached ? 'success' : 'default'" size="small">
                {{ wordSimStats.vocabCached ? '已缓存' : '未缓存' }}
              </NTag>
              <template #suffix v-if="wordSimStats.vocabCached">
                <span class="stat-suffix">{{ wordSimStats.cachedChunks }} chunks</span>
              </template>
            </NStatistic>
          </NCard>
        </NGridItem>
      </NGrid>

      <NCard title="📊 分块分布图" class="chunk-dashboard-card">
        <NGrid :cols="5" :x-gap="16" :y-gap="16">
          <NGridItem>
            <div class="mini-chart">
              <div class="mini-chart-header">
                <span class="mini-chart-title">📚 诗词</span>
                <NTag size="small" :type="poemStats.cachedChunkIds.length === poemStats.totalChunks && poemStats.totalChunks > 0 ? 'success' : 'default'">
                  {{ poemStats.cachedChunkIds.length }} / {{ poemStats.totalChunks }}
                </NTag>
              </div>
              <div class="mini-chart-body">
                <div v-if="poemChunkBars.length > 0" class="mini-bars">
                  <div
                    v-for="bar in poemChunkBars"
                    :key="bar.id"
                    class="mini-bar"
                    :class="{ 'cached': bar.cached }"
                    :style="{ height: maxPoemCount > 0 ? (bar.count / maxPoemCount * 100) + '%' : '0%' }"
                    :title="`分块 ${bar.id}: ${bar.count} 首${bar.cached ? ' (已缓存)' : ''}`"
                  />
                </div>
                <NEmpty v-else description="暂无数据" size="small" />
              </div>
              <div class="mini-chart-legend">
                <span class="legend-dot cached"></span> 已缓存
                <span class="legend-dot uncached"></span> 未下载
              </div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="mini-chart">
              <div class="mini-chart-header">
                <span class="mini-chart-title">👤 诗人</span>
                <NTag size="small" :type="authorStats.cachedChunkIds.length === authorStats.totalChunks && authorStats.totalChunks > 0 ? 'success' : 'default'">
                  {{ authorStats.cachedChunkIds.length }} / {{ authorStats.totalChunks }}
                </NTag>
              </div>
              <div class="mini-chart-body">
                <div v-if="authorChunkBars.length > 0" class="mini-bars">
                  <div
                    v-for="bar in authorChunkBars"
                    :key="bar.id"
                    class="mini-bar author"
                    :class="{ 'cached': bar.cached }"
                    :style="{ height: maxAuthorCount > 0 ? (bar.count / maxAuthorCount * 100) + '%' : '0%' }"
                    :title="`分块 ${bar.id}: ${bar.count} 位${bar.cached ? ' (已缓存)' : ''}`"
                  />
                </div>
                <NEmpty v-else description="暂无数据" size="small" />
              </div>
              <div class="mini-chart-legend">
                <span class="legend-dot cached author"></span> 已缓存
                <span class="legend-dot uncached"></span> 未下载
              </div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="mini-chart">
              <div class="mini-chart-header">
                <span class="mini-chart-title">📊 词频</span>
                <NTag size="small" :type="wordcountStats.cachedChunkIds.length === wordcountStats.totalChunks && wordcountStats.totalChunks > 0 ? 'success' : 'default'">
                  {{ wordcountStats.cachedChunkIds.length }} / {{ wordcountStats.totalChunks }}
                </NTag>
              </div>
              <div class="mini-chart-body">
                <div v-if="wordcountChunkBars.length > 0" class="mini-bars">
                  <div
                    v-for="bar in wordcountChunkBars"
                    :key="bar.id"
                    class="mini-bar wordcount"
                    :class="{ 'cached': bar.cached }"
                    :style="{ height: maxWordcountCount > 0 ? (bar.count / maxWordcountCount * 100) + '%' : '0%' }"
                    :title="`分块 ${bar.id}: ${bar.count} 词${bar.cached ? ' (已缓存)' : ''}`"
                  />
                </div>
                <NEmpty v-else description="暂无数据" size="small" />
              </div>
              <div class="mini-chart-legend">
                <span class="legend-dot cached wordcount"></span> 已缓存
                <span class="legend-dot uncached"></span> 未下载
              </div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="mini-chart">
              <div class="mini-chart-header">
                <span class="mini-chart-title">🔗 词境</span>
                <NTag size="small" :type="wordSimStats.vocabCached ? 'success' : 'default'">
                  {{ wordSimStats.cachedChunks }} / {{ wordSimStats.totalChunks }}
                </NTag>
              </div>
              <div class="mini-chart-body">
                <div v-if="wordSimChunkBars.length > 0" class="mini-bars">
                  <div
                    v-for="bar in wordSimChunkBars"
                    :key="bar.id"
                    class="mini-bar wordsim"
                    :class="{ 'cached': bar.cached }"
                    :style="{ height: maxWordSimCount > 0 ? (bar.count / maxWordSimCount * 100) + '%' : '0%' }"
                    :title="`分块 ${bar.id}: ${bar.count} 词${bar.cached ? ' (已缓存)' : ''}`"
                  />
                </div>
                <NEmpty v-else description="暂无数据" size="small" />
              </div>
              <div class="mini-chart-legend">
                <span class="legend-dot cached wordsim"></span> 已缓存
                <span class="legend-dot uncached"></span> 未下载
              </div>
            </div>
          </NGridItem>

          <NGridItem>
            <div class="mini-chart">
              <div class="mini-chart-header">
                <span class="mini-chart-title">🔍 搜索索引</span>
                <NTag size="small" :type="searchIndexStats.loaded && searchIndexStats.cachedPrefixes > 0 ? 'success' : 'default'">
                  {{ searchIndexStats.cachedPrefixes }} / {{ searchIndexStats.totalPrefixes }}
                </NTag>
              </div>
              <div class="mini-chart-body">
                <div v-if="searchIndexChunkBars.length > 0" class="mini-bars">
                  <div
                    v-for="bar in searchIndexChunkBars"
                    :key="bar.id"
                    class="mini-bar searchindex"
                    :class="{ 'cached': bar.cached }"
                    :style="{ height: maxSearchIndexCount > 0 ? (bar.count / maxSearchIndexCount * 100) + '%' : '0%' }"
                    :title="`前缀组 ${bar.id}: ${bar.count} 个前缀${bar.cached ? ' (已缓存)' : ''}`"
                  />
                </div>
                <NEmpty v-else description="暂无数据" size="small" />
              </div>
              <div class="mini-chart-legend">
                <span class="legend-dot cached searchindex"></span> 已缓存
                <span class="legend-dot uncached"></span> 未下载
              </div>
            </div>
          </NGridItem>
        </NGrid>
      </NCard>

      <NCard title="快速操作">
        <NSpace>
          <NButton type="primary" @click="emit('switch-tab', 'download')">
            <template #icon>
              <CloudDownloadOutline />
            </template>
            下载数据
          </NButton>
          <NButton type="error" ghost @click="handleClearCache">
            <template #icon>
              <TrashOutline />
            </template>
            清空缓存
          </NButton>
          <NButton @click="emit('refresh')">
            <template #icon>
              <SpeedometerOutline />
            </template>
            刷新状态
          </NButton>
        </NSpace>
      </NCard>
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

.legend-dot.uncached {
  background: #e8e8e8;
}
</style>
