<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import {
  NCard, NGrid, NGridItem, NProgress, NButton,
  NSpace, NTag, NTabs, NTabPane, NEmpty, NDivider, NSpin, NSkeleton
} from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'

import { getAllStorageStats, getBrowserStorageInfo, getStorageStats, getMetadata, getCache, type StorageStats, type BrowserStorageInfo } from '@/composables/useCacheV2'
import { WORD_SIMILARITY_STORAGE, POEM_INDEX_STORAGE } from '@/composables/useMetadataLoader'
import { useKeywordIndex } from '@/composables/useKeywordIndex'

const props = defineProps<{
  isLoadingStats?: boolean
}>()

const isLoading = ref(false)
const loadingStep = ref('')
const loadProgress = ref(0)

const loadingState = reactive({
  browserInfo: false,
  wordSim: false,
  searchIndex: false,
  keywordIndex: false,
  storageStats: false
})

const storageStats = ref<StorageStats[]>([])
const browserStorageInfo = ref<BrowserStorageInfo | null>(null)
const selectedStorage = ref<string>('')
const selectedStorageDetail = ref<StorageStats | null>(null)

const wordSimStats = ref({
  vocabCached: false,
  vocabSize: 0,
  cachedChunks: 0,
  totalChunks: 0
})

const searchIndexStats = ref({
  cachedPrefixes: 0,
  totalPrefixes: 0,
  loaded: false
})

const keywordIndexStats = ref({
  cachedChunks: 0,
  totalChunks: 0,
  loaded: false
})

const keywordIndex = useKeywordIndex()

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const updateProgress = async (step: string, stateKey: keyof typeof loadingState, progress: number) => {
  loadingStep.value = step
  loadingState[stateKey] = true
  loadProgress.value = progress
  await delay(50)
}

const resetLoadingState = () => {
  loadingState.browserInfo = false
  loadingState.wordSim = false
  loadingState.searchIndex = false
  loadingState.keywordIndex = false
  loadingState.storageStats = false
}

const loadStorageDetails = async () => {
  resetLoadingState()
  
  isLoading.value = true
  loadProgress.value = 0
  loadingStep.value = '正在初始化...'
  await delay(100)
  
  try {
    loadingStep.value = '正在获取浏览器存储信息...'
    await delay(50)
    storageStats.value = await getAllStorageStats()
    await delay(30)
    browserStorageInfo.value = await getBrowserStorageInfo()
    await updateProgress('词境数据加载中...', 'browserInfo', 20)
  } catch (e) {
    console.error('Failed to load storage details:', e)
  }

  try {
    loadingStep.value = '正在加载词境数据...'
    await delay(50)
    const { useWordSimilarityMetadata, usePoemIndexManifest } = await import('@/composables/useMetadataLoader')
    const wsMeta = useWordSimilarityMetadata()
    const piMeta = usePoemIndexManifest()

    await delay(30)
    const wordSimMetaData = await wsMeta.loadMetadata()
    wordSimStats.value.totalChunks = wordSimMetaData?.total_chunks || 0
    wordSimStats.value.vocabSize = wordSimMetaData?.vocab_size || 0
    await delay(30)

    const wordSimVocab = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')
    if (wordSimVocab && Object.keys(wordSimVocab).length > 0) {
      wordSimStats.value.vocabCached = true
    }
    await delay(30)

    const wordSimMetaStored = await getMetadata(WORD_SIMILARITY_STORAGE)
    if (wordSimMetaStored && wordSimMetaStored.loadedChunkIds) {
      const validIds = wordSimMetaStored.loadedChunkIds.filter((id: number) => id < (wordSimMetaStored.totalChunks || 0))
      wordSimStats.value.cachedChunks = validIds.length
    }
    await updateProgress('搜索索引加载中...', 'wordSim', 45)

    await delay(50)
    const searchIndexMetaData = await piMeta.loadMetadata()
    searchIndexStats.value.totalPrefixes = Object.keys(searchIndexMetaData?.prefixMap || {}).length
    await delay(30)

    const searchIndexPrefixes = await getCache<string[]>(POEM_INDEX_STORAGE, 'loaded-prefixes')
    if (searchIndexPrefixes) {
      searchIndexStats.value.cachedPrefixes = searchIndexPrefixes.length
      searchIndexStats.value.loaded = true
    }
    await updateProgress('关键词索引加载中...', 'searchIndex', 70)

    await delay(50)
    const keywordMeta = await keywordIndex.loadMetadata()
    keywordIndexStats.value.totalChunks = keywordMeta.total_chunks || 201
    keywordIndexStats.value.cachedChunks = keywordMeta.loadedChunkIds?.length || 0
    keywordIndexStats.value.loaded = keywordIndexStats.value.cachedChunks > 0
    await updateProgress('计算存储统计...', 'keywordIndex', 85)

    await delay(50)
    storageStats.value = await getAllStorageStats()
    loadingState.storageStats = true
    loadProgress.value = 100
    
    loadingStep.value = '加载完成'
  } catch (e) {
    console.error('Failed to load metadata:', e)
    loadingStep.value = '加载失败'
  } finally {
    await delay(300)
    isLoading.value = false
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

defineExpose({
  loadStorageDetails
})
</script>

<template>
  <div class="storage-view">
    <div v-if="isLoading" class="loading-overlay">
      <NCard class="loading-card">
        <div class="loading-content">
          <NSpin size="large" />
          <div class="loading-progress">
            <NProgress
              type="line"
              :percentage="loadProgress"
              :indicator-placement="'inside'"
              :processing="loadProgress < 100"
            />
          </div>
          <div class="loading-step">{{ loadingStep }}</div>
          <div class="loading-states">
            <div class="loading-state-item" :class="{ done: loadingState.browserInfo }">
              <span class="state-icon">{{ loadingState.browserInfo ? '✓' : '○' }}</span>
              浏览器存储
            </div>
            <div class="loading-state-item" :class="{ done: loadingState.wordSim }">
              <span class="state-icon">{{ loadingState.wordSim ? '✓' : '○' }}</span>
              词境数据
            </div>
            <div class="loading-state-item" :class="{ done: loadingState.searchIndex }">
              <span class="state-icon">{{ loadingState.searchIndex ? '✓' : '○' }}</span>
              搜索索引
            </div>
            <div class="loading-state-item" :class="{ done: loadingState.keywordIndex }">
              <span class="state-icon">{{ loadingState.keywordIndex ? '✓' : '○' }}</span>
              关键词索引
            </div>
          </div>
        </div>
      </NCard>
    </div>

    <NSpace v-else vertical size="large">
      <div class="refresh-bar">
        <NButton quaternary @click="loadStorageDetails">
          <template #icon>
            <RefreshOutline />
          </template>
          刷新
        </NButton>
      </div>

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

    <NCard v-if="browserStorageInfo?.localStorage.items.length" title="💾 LocalStorage 详情">
      <div class="detail-list">
        <div v-for="item in browserStorageInfo.localStorage.items" :key="item.key" class="detail-item">
          <span class="detail-item-name">{{ item.key }}</span>
          <NTag size="small">{{ formatBytes(item.size) }}</NTag>
        </div>
      </div>
    </NCard>

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
  </div>
</template>

<style scoped>
.storage-overview-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f8f8;
  border-radius: 8px;
}

.storage-icon {
  font-size: 28px;
}

.storage-info {
  flex: 1;
}

.storage-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.storage-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.storage-detail {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.quota-info {
  margin-top: 8px;
}

.quota-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}

.quota-value {
  font-weight: 500;
  color: #333;
}

.storage-detail-card {
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 12px;
}

.storage-detail-card:hover {
  border-color: #8b2635;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.storage-detail-card .detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.storage-detail-card .detail-title {
  font-weight: 600;
  font-size: 14px;
}

.storage-detail-card .detail-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.storage-detail-card .detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.storage-detail-card .detail-label {
  color: #666;
}

.storage-detail-card .detail-value {
  font-weight: 500;
  color: #333;
}

.storage-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.storage-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

.storage-detail-body {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.storage-metric {
  font-size: 13px;
}

.metric-label {
  color: #666;
}

.metric-value {
  color: #333;
  font-weight: 500;
}

.storage-detail-footer {
  text-align: right;
}

.keyword-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.keyword-stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f8f8;
  border-radius: 6px;
}

.keyword-stat-label {
  font-size: 13px;
  color: #666;
}

.keyword-stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.detail-list {
  max-height: 400px;
  overflow-y: auto;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
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

.storage-view {
  position: relative;
  min-height: 400px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 100;
}

.loading-card {
  width: 400px;
  max-width: 90%;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px 0;
}

.loading-progress {
  width: 100%;
}

.loading-step {
  font-size: 14px;
  color: #666;
}

.loading-states {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
}

.loading-state-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 13px;
  color: #999;
  transition: all 0.3s;
}

.loading-state-item.done {
  background: #e8f5e9;
  color: #4caf50;
}

.state-icon {
  font-size: 14px;
}

.refresh-bar {
  display: flex;
  justify-content: flex-end;
}
</style>
