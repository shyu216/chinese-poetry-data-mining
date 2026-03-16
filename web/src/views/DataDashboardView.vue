<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NCard, NGrid, NGridItem, NStatistic, NButton, NProgress,
  NSpace, NTag, NAlert, NTabs, NTabPane,
  NEmpty, NSpin, NNumberAnimation, NDivider
} from 'naive-ui'
import {
  BookOutline, PersonOutline, BarChartOutline,
  DownloadOutline, TrashOutline,
  CloudDownloadOutline, ServerOutline, SpeedometerOutline,
  GitNetworkOutline, SearchOutline
} from '@vicons/ionicons5'

import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { useWordcountV2 } from '@/composables/useWordcountV2'
import { useSearchIndexV2 } from '@/composables/useSearchIndexV2'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { usePoemsMetadata, useAuthorsMetadata, useWordcountMetadata, usePoemIndexManifest, useWordSimilarityMetadata, POEMS_STORAGE, AUTHORS_STORAGE, WORDCOUNT_STORAGE, POEM_INDEX_STORAGE, WORD_SIMILARITY_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata, clearStorage, getCache, getStorageStats, getAllStorageStats, getBrowserStorageInfo, type StorageStats, type BrowserStorageInfo } from '@/composables/useCacheV2'
import type { PoemsIndex, AuthorsIndex, WordCountMeta } from '@/composables/types'

const poemsV2 = usePoemsV2()
const authorsV2 = useAuthorsV2()
const wordcountV2 = useWordcountV2()
const searchIndexV2 = useSearchIndexV2()
const wordSimilarityV2 = useWordSimilarityV2()

const poemsMeta = usePoemsMetadata()
const authorsMeta = useAuthorsMetadata()
const wordcountMeta = useWordcountMetadata()
const poemIndexMeta = usePoemIndexManifest()
const wordSimMeta = useWordSimilarityMetadata()

const activeTab = ref('overview')
const isLoadingStats = ref(false)

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

const storageStats = ref<StorageStats[]>([])
const browserStorageInfo = ref<BrowserStorageInfo | null>(null)
const selectedStorage = ref<string>('')
const selectedStorageDetail = ref<StorageStats | null>(null)

const downloadState = ref({
  poems: { isDownloading: false, progress: 0, status: '' },
  authors: { isDownloading: false, progress: 0, status: '' },
  wordcount: { isDownloading: false, progress: 0, status: '' },
  searchIndex: { isDownloading: false, progress: 0, status: '' },
  wordSim: { isDownloading: false, progress: 0, status: '' }
})

const loadStorageDetails = async () => {
  try {
    storageStats.value = await getAllStorageStats()
    browserStorageInfo.value = await getBrowserStorageInfo()
  } catch (e) {
    console.error('Failed to load storage details:', e)
  }
}

const viewStorageDetail = async (storage: string) => {
  selectedStorage.value = storage
  selectedStorageDetail.value = await getStorageStats(storage)
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const loadStats = async () => {
  isLoadingStats.value = true
  try {
    await loadStorageDetails()
    
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

    const wordSimVocab = await getCache<number[]>(WORD_SIMILARITY_STORAGE, 'vocab')
    if (wordSimVocab && wordSimVocab.length > 0) {
      wordSimStats.value.vocabCached = true
    }

    const wordSimMetaStored = await getMetadata(WORD_SIMILARITY_STORAGE)
    if (wordSimMetaStored) {
      wordSimStats.value.cachedChunks = wordSimMetaStored.loadedChunkIds?.length || 0
    }
  } finally {
    isLoadingStats.value = false
  }
}

const downloadAll = async (type: string) => {
  const state = downloadState.value[type as keyof typeof downloadState.value]
  state.isDownloading = true
  state.progress = 0

  try {
    switch (type) {
      case 'poems':
        await downloadPoems(state)
        break
      case 'authors':
        await downloadAuthors(state)
        break
      case 'wordcount':
        await downloadWordcount(state)
        break
      case 'searchIndex':
        await downloadSearchIndex(state)
        break
      case 'wordSim':
        await downloadWordSim(state)
        break
    }
    await loadStats()
  } catch (e) {
    state.status = '下载失败: ' + (e as Error).message
  } finally {
    state.isDownloading = false
  }
}

const downloadPoems = async (state: { progress: number; status: string }) => {
  const index = await poemsMeta.loadMetadata()
  const totalChunks = index?.metadata?.chunks || 0

  for (let i = 0; i < totalChunks; i++) {
    state.status = `正在下载诗词分块 ${i + 1}/${totalChunks}...`
    await poemsV2.loadChunkSummaries(i)
    state.progress = Math.round(((i + 1) / totalChunks) * 100)
    if (i % 10 === 0) await new Promise(resolve => setTimeout(resolve, 0))
  }
  state.status = '下载完成！'
}

const downloadAuthors = async (state: { progress: number; status: string }) => {
  const index = await authorsMeta.loadMetadata()
  const totalChunks = index?.total || 0

  for (let i = 0; i < totalChunks; i++) {
    state.status = `正在下载诗人分块 ${i + 1}/${totalChunks}...`
    await authorsV2.loadAuthorChunk(i)
    state.progress = Math.round(((i + 1) / totalChunks) * 100)
    if (i % 5 === 0) await new Promise(resolve => setTimeout(resolve, 0))
  }
  state.status = '下载完成！'
}

const downloadWordcount = async (state: { progress: number; status: string }) => {
  const index = await wordcountMeta.loadMetadata()
  const totalChunks = index?.total_chunks || 0

  for (let i = 0; i < totalChunks; i++) {
    state.status = `正在下载词频分块 ${i + 1}/${totalChunks}...`
    await wordcountV2.loadChunk(i)
    state.progress = Math.round(((i + 1) / totalChunks) * 100)
    if (i % 10 === 0) await new Promise(resolve => setTimeout(resolve, 0))
  }
  state.status = '下载完成！'
}

const downloadSearchIndex = async (state: { progress: number; status: string }) => {
  const manifest = await poemIndexMeta.loadMetadata()
  const prefixes = Object.keys(manifest?.prefixMap || {})
  const totalPrefixes = prefixes.length

  for (let i = 0; i < totalPrefixes; i++) {
    state.status = `正在下载搜索分块 ${i + 1}/${totalPrefixes}...`
    await searchIndexV2.loadPoemChunk(prefixes[i]!)
    state.progress = Math.round(((i + 1) / totalPrefixes) * 100)
    if (i % 10 === 0) await new Promise(resolve => setTimeout(resolve, 0))
  }
  state.status = '下载完成！'
}

const downloadWordSim = async (state: { progress: number; status: string }) => {
  state.status = '正在加载词表...'
  await wordSimilarityV2.loadVocab()
  state.progress = 10

  const metadata = await wordSimMeta.loadMetadata()
  const vocabSize = metadata?.vocab_size || 0
  const totalChunks = metadata?.total_chunks || 0
  const wordsPerChunk = Math.ceil(vocabSize / totalChunks)
  const wordIds = Array.from({ length: vocabSize }, (_, i) => i)
  const batchSize = 20

  for (let i = 0; i < totalChunks; i += batchSize) {
    const startWordId = i * wordsPerChunk
    const endWordId = Math.min((i + batchSize) * wordsPerChunk, vocabSize)
    const batch = wordIds.slice(startWordId, endWordId)
    state.status = `已下载 ${Math.min(i + batchSize, totalChunks)}/${totalChunks} 个分块...`
    await wordSimilarityV2.preloadChunks(batch)
    state.progress = Math.round(10 + ((Math.min(i + batchSize, totalChunks) / totalChunks) * 90))
    if (i % 10 === 0) await new Promise(resolve => setTimeout(resolve, 0))
  }
  state.status = '下载完成！'
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

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="data-dashboard-v2">
    <header class="page-header">
      <h1 class="page-title">
        <ServerOutline class="title-icon" />
        数据管理中心
      </h1>
      <p class="page-subtitle">
        管理本地缓存数据，支持离线浏览
      </p>
    </header>

    <NTabs v-model:value="activeTab" type="line" size="large" class="dashboard-tabs">
      <NTabPane name="overview" tab="总览">
        <NSpin :show="isLoadingStats">
          <NSpace vertical size="large">
            <!-- 统计卡片 -->
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

            <!-- 分块分布图 -->
            <NCard title="📊 分块分布图" class="chunk-dashboard-card">
              <NGrid :cols="3" :x-gap="16" :y-gap="16">
                <!-- 诗词分块 -->
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

                <!-- 诗人分块 -->
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

                <!-- 词频分块 -->
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
              </NGrid>
            </NCard>

            <!-- 快速操作 -->
            <NCard title="快速操作">
              <NSpace>
                <NButton type="primary" @click="activeTab = 'download'">
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
                <NButton @click="loadStats">
                  <template #icon>
                    <SpeedometerOutline />
                  </template>
                  刷新状态
                </NButton>
              </NSpace>
            </NCard>
          </NSpace>
        </NSpin>
      </NTabPane>

      <NTabPane name="download" tab="数据下载">
        <NSpace vertical size="large">
          <NCard title="📚 诗词数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              诗词数据库包含 {{ poemStats.totalChunks }} 个分块的诗词摘要数据。
            </NAlert>
            <NProgress
              type="line"
              :percentage="poemStats.totalChunks > 0 ? Math.round(poemStats.cachedChunkIds.length / poemStats.totalChunks * 100) : 0"
              :indicator-placement="'inside'"
              :status="poemStats.cachedChunkIds.length === poemStats.totalChunks && poemStats.totalChunks > 0 ? 'success' : 'default'"
              style="margin-bottom: 12px;"
            />
            <NButton
              type="primary"
              size="large"
              :loading="downloadState.poems.isDownloading"
              :disabled="downloadState.poems.isDownloading || poemStats.cachedChunkIds.length === poemStats.totalChunks"
              @click="downloadAll('poems')"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ downloadState.poems.isDownloading ? downloadState.poems.status : (poemStats.cachedChunkIds.length === poemStats.totalChunks ? '已全部下载' : '下载全部诗词数据') }}
            </NButton>
            <NProgress
              v-if="downloadState.poems.isDownloading"
              type="line"
              :percentage="downloadState.poems.progress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>

          <NCard title="👥 诗人数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              诗人数据库包含 {{ authorStats.totalChunks }} 个分块的诗人统计数据。
            </NAlert>
            <NProgress
              type="line"
              :percentage="authorStats.totalChunks > 0 ? Math.round(authorStats.cachedChunkIds.length / authorStats.totalChunks * 100) : 0"
              :indicator-placement="'inside'"
              :status="authorStats.cachedChunkIds.length === authorStats.totalChunks && authorStats.totalChunks > 0 ? 'success' : 'default'"
              style="margin-bottom: 12px;"
            />
            <NButton
              type="primary"
              size="large"
              :loading="downloadState.authors.isDownloading"
              :disabled="downloadState.authors.isDownloading || authorStats.cachedChunkIds.length === authorStats.totalChunks"
              @click="downloadAll('authors')"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ downloadState.authors.isDownloading ? downloadState.authors.status : (authorStats.cachedChunkIds.length === authorStats.totalChunks ? '已全部下载' : '下载全部诗人数据') }}
            </NButton>
            <NProgress
              v-if="downloadState.authors.isDownloading"
              type="line"
              :percentage="downloadState.authors.progress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>

          <NCard title="📊 词频统计数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              词频数据库包含 {{ wordcountStats.totalChunks }} 个分块的词频统计数据。
            </NAlert>
            <NProgress
              type="line"
              :percentage="wordcountStats.totalChunks > 0 ? Math.round(wordcountStats.cachedChunkIds.length / wordcountStats.totalChunks * 100) : 0"
              :indicator-placement="'inside'"
              :status="wordcountStats.cachedChunkIds.length === wordcountStats.totalChunks && wordcountStats.totalChunks > 0 ? 'success' : 'default'"
              style="margin-bottom: 12px;"
            />
            <NButton
              type="primary"
              size="large"
              :loading="downloadState.wordcount.isDownloading"
              :disabled="downloadState.wordcount.isDownloading || wordcountStats.cachedChunkIds.length === wordcountStats.totalChunks"
              @click="downloadAll('wordcount')"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ downloadState.wordcount.isDownloading ? downloadState.wordcount.status : (wordcountStats.cachedChunkIds.length === wordcountStats.totalChunks ? '已全部下载' : '下载全部词频数据') }}
            </NButton>
            <NProgress
              v-if="downloadState.wordcount.isDownloading"
              type="line"
              :percentage="downloadState.wordcount.progress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>

          <NCard title="🔍 搜索索引数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              搜索索引包含 {{ searchIndexStats.totalPrefixes }} 个前缀分块的诗词数据。
            </NAlert>
            <NProgress
              type="line"
              :percentage="searchIndexStats.totalPrefixes > 0 ? Math.round(searchIndexStats.cachedPrefixes / searchIndexStats.totalPrefixes * 100) : 0"
              :indicator-placement="'inside'"
              :status="searchIndexStats.cachedPrefixes === searchIndexStats.totalPrefixes && searchIndexStats.totalPrefixes > 0 ? 'success' : 'default'"
              style="margin-bottom: 12px;"
            />
            <NButton
              type="primary"
              size="large"
              :loading="downloadState.searchIndex.isDownloading"
              :disabled="downloadState.searchIndex.isDownloading || searchIndexStats.cachedPrefixes === searchIndexStats.totalPrefixes"
              @click="downloadAll('searchIndex')"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ downloadState.searchIndex.isDownloading ? downloadState.searchIndex.status : (searchIndexStats.cachedPrefixes === searchIndexStats.totalPrefixes ? '已全部下载' : '下载全部搜索索引') }}
            </NButton>
            <NProgress
              v-if="downloadState.searchIndex.isDownloading"
              type="line"
              :percentage="downloadState.searchIndex.progress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>

          <NCard title="🔗 词境探索数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              词境探索数据库包含 {{ wordSimStats.vocabSize.toLocaleString() }} 个词汇的相似度数据，共 {{ wordSimStats.totalChunks }} 个分块。
            </NAlert>
            <NProgress
              type="line"
              :percentage="wordSimStats.totalChunks > 0 && wordSimStats.vocabCached ? Math.round(wordSimStats.cachedChunks / wordSimStats.totalChunks * 100) : 0"
              :indicator-placement="'inside'"
              :status="wordSimStats.vocabCached && wordSimStats.cachedChunks === wordSimStats.totalChunks ? 'success' : 'default'"
              style="margin-bottom: 12px;"
            />
            <NButton
              type="primary"
              size="large"
              :loading="downloadState.wordSim.isDownloading"
              :disabled="downloadState.wordSim.isDownloading || (wordSimStats.vocabCached && wordSimStats.cachedChunks === wordSimStats.totalChunks)"
              @click="downloadAll('wordSim')"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ downloadState.wordSim.isDownloading ? downloadState.wordSim.status : (wordSimStats.vocabCached && wordSimStats.cachedChunks === wordSimStats.totalChunks ? '已全部下载' : '下载全部词境数据') }}
            </NButton>
            <NProgress
              v-if="downloadState.wordSim.isDownloading"
              type="line"
              :percentage="downloadState.wordSim.progress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>
        </NSpace>
      </NTabPane>

      <NTabPane name="storage" tab="存储详情">
        <NSpace vertical size="large">
          <!-- 浏览器存储概览 -->
          <NCard title="🌐 浏览器存储概览">
            <NGrid :cols="4" :x-gap="16" :y-gap="16">
              <NGridItem>
                <div class="storage-overview-item">
                  <div class="storage-icon">🗄️</div>
                  <div class="storage-info">
                    <div class="storage-label">IndexedDB</div>
                    <div class="storage-value">{{ formatBytes(browserStorageInfo?.indexedDB.estimatedSize || 0) }}</div>
                    <div class="storage-detail">{{ browserStorageInfo?.indexedDB.objectStores.length || 0 }} 个对象存储</div>
                  </div>
                </div>
              </NGridItem>
              <NGridItem>
                <div class="storage-overview-item">
                  <div class="storage-icon">💾</div>
                  <div class="storage-info">
                    <div class="storage-label">LocalStorage</div>
                    <div class="storage-value">{{ formatBytes(browserStorageInfo?.localStorage.estimatedSize || 0) }}</div>
                    <div class="storage-detail">{{ browserStorageInfo?.localStorage.itemCount || 0 }} 个条目</div>
                  </div>
                </div>
              </NGridItem>
              <NGridItem>
                <div class="storage-overview-item">
                  <div class="storage-icon">📋</div>
                  <div class="storage-info">
                    <div class="storage-label">SessionStorage</div>
                    <div class="storage-value">{{ formatBytes(browserStorageInfo?.sessionStorage.estimatedSize || 0) }}</div>
                    <div class="storage-detail">{{ browserStorageInfo?.sessionStorage.itemCount || 0 }} 个条目</div>
                  </div>
                </div>
              </NGridItem>
              <NGridItem>
                <div class="storage-overview-item">
                  <div class="storage-icon">🍪</div>
                  <div class="storage-info">
                    <div class="storage-label">Cookies</div>
                    <div class="storage-value">{{ browserStorageInfo?.cookies.length || 0 }} 个</div>
                    <div class="storage-detail">当前域名</div>
                  </div>
                </div>
              </NGridItem>
            </NGrid>

            <NDivider />

            <div v-if="browserStorageInfo?.quota" class="quota-info">
              <div class="quota-header">
                <span>存储配额使用情况</span>
                <span class="quota-value">{{ formatBytes(browserStorageInfo.quota.usage) }} / {{ formatBytes(browserStorageInfo.quota.quota) }}</span>
              </div>
              <NProgress
                type="line"
                :percentage="Math.round((browserStorageInfo.quota.usage / browserStorageInfo.quota.quota) * 100)"
                :indicator-placement="'inside'"
                :status="(browserStorageInfo.quota.usage / browserStorageInfo.quota.quota) > 0.8 ? 'warning' : 'default'"
                :height="20"
              />
            </div>
          </NCard>

          <!-- 各存储空间详情 -->
          <NCard title="📦 缓存存储详情">
            <NEmpty v-if="storageStats.length === 0" description="暂无缓存数据" />
            <NGrid v-else :cols="2" :x-gap="16" :y-gap="16">
              <NGridItem v-for="stats in storageStats" :key="stats.storage">
                <div class="storage-detail-card" @click="viewStorageDetail(stats.storage)">
                  <div class="storage-detail-header">
                    <span class="storage-name">{{ stats.storage }}</span>
                    <NTag size="small" :type="stats.totalSize > 0 ? 'success' : 'default'">
                      {{ formatBytes(stats.totalSize) }}
                    </NTag>
                  </div>
                  <div class="storage-detail-body">
                    <div class="storage-metric">
                      <span class="metric-label">分块:</span>
                      <span class="metric-value">{{ stats.chunkCount }} 个</span>
                    </div>
                    <div class="storage-metric">
                      <span class="metric-label">缓存项:</span>
                      <span class="metric-value">{{ stats.cacheCount }} 个</span>
                    </div>
                  </div>
                  <div class="storage-detail-footer">
                    <NButton text size="small" type="primary">查看详情 →</NButton>
                  </div>
                </div>
              </NGridItem>
            </NGrid>
          </NCard>

          <!-- 选中存储的详细列表 -->
          <NCard v-if="selectedStorageDetail" :title="`📂 ${selectedStorageDetail.storage} 详情`">
            <template #header-extra>
              <NButton text size="small" @click="selectedStorageDetail = null; selectedStorage = ''">
                关闭
              </NButton>
            </template>

            <NTabs type="segment">
              <NTabPane name="chunks" :tab="`分块 (${selectedStorageDetail.chunks.length})`">
                <div class="detail-list">
                  <div v-for="chunk in selectedStorageDetail.chunks" :key="chunk.chunkId" class="detail-item">
                    <div class="detail-item-info">
                      <span class="detail-item-name">分块 #{{ chunk.chunkId }}</span>
                      <span class="detail-item-time">{{ new Date(chunk.timestamp).toLocaleString() }}</span>
                    </div>
                    <NTag size="small" type="info">{{ formatBytes(chunk.size) }}</NTag>
                  </div>
                </div>
              </NTabPane>
              <NTabPane name="caches" :tab="`缓存项 (${selectedStorageDetail.caches.length})`">
                <div class="detail-list">
                  <div v-for="cache in selectedStorageDetail.caches" :key="cache.key" class="detail-item">
                    <div class="detail-item-info">
                      <span class="detail-item-name">{{ cache.key }}</span>
                      <span class="detail-item-time">{{ new Date(cache.timestamp).toLocaleString() }}</span>
                    </div>
                    <NTag size="small" type="info">{{ formatBytes(cache.size) }}</NTag>
                  </div>
                </div>
              </NTabPane>
            </NTabs>
          </NCard>

          <!-- LocalStorage 详情 -->
          <NCard v-if="browserStorageInfo?.localStorage.items.length" title="💾 LocalStorage 详情">
            <div class="detail-list">
              <div v-for="item in browserStorageInfo.localStorage.items" :key="item.key" class="detail-item">
                <span class="detail-item-name">{{ item.key }}</span>
                <NTag size="small">{{ formatBytes(item.size) }}</NTag>
              </div>
            </div>
          </NCard>

          <!-- Cookies 详情 -->
          <NCard v-if="browserStorageInfo?.cookies.length" title="🍪 Cookies 详情">
            <div class="detail-list">
              <div v-for="cookie in browserStorageInfo.cookies" :key="cookie.name" class="detail-item">
                <div class="detail-item-info">
                  <span class="detail-item-name">{{ cookie.name }}</span>
                  <span class="detail-item-time">{{ cookie.domain }}</span>
                </div>
                <NTag size="small">{{ formatBytes(cookie.size) }}</NTag>
              </div>
            </div>
          </NCard>
        </NSpace>
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.data-dashboard-v2 {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  width: 32px;
  height: 32px;
  color: #8b2635;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
}

.dashboard-tabs {
  margin-top: 24px;
}

/* 统计卡片 */
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

/* 分块分布图 */
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

.legend-dot.uncached {
  background: #e8e8e8;
}

/* 下载卡片 */
.download-card {
  transition: all 0.3s ease;
}

.download-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

/* 存储详情样式 */
.storage-overview-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f8f8;
  border-radius: 8px;
}

.storage-icon {
  font-size: 32px;
}

.storage-info {
  flex: 1;
}

.storage-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.storage-value {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.storage-detail {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

.quota-info {
  margin-top: 16px;
}

.quota-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.quota-value {
  font-weight: 500;
  color: #333;
}

.storage-detail-card {
  background: #f8f8f8;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.storage-detail-card:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

.storage-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.storage-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.storage-detail-body {
  display: flex;
  gap: 24px;
}

.storage-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 11px;
  color: #999;
}

.metric-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.storage-detail-footer {
  margin-top: 12px;
  text-align: right;
}

.detail-list {
  max-height: 300px;
  overflow-y: auto;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-item-name {
  font-size: 13px;
  color: #333;
}

.detail-item-time {
  font-size: 11px;
  color: #999;
}
</style>
