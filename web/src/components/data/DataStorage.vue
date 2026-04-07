<!--
  @overview
  file: web/src/components/data/DataStorage.vue
  category: frontend-component / data-management
  tech: Vue 3 + TypeScript + Naive UI
  summary: 数据存储概览组件，负责读取并展示浏览器存储（IndexedDB）与已缓存数据的统计与进度信息。

  Data pipeline:
  - 读取: 使用 `useCache` 的工具函数读取不同存储键（poems/authors/wordcount/word-similarity/poem-index 等）的元数据与统计
  - 处理: 聚合各类统计、更新局部加载状态并在 UI 中显示进度（NProgress/NSpin）
  - 交互: 支持清理缓存、刷新统计、展示单分块详情并触发下载/删除操作

  Complexity & notes:
  - 大多数统计读取为 O(1) 或 O(#storedChunks)；遍历所有存储统计为 O(m)，m = 存储项种类数
  - 对于大型存储（大量 chunk）建议逐页或异步加载统计以避免主线程阻塞

  Potential issues & recommendations:
  - 在读取大量存储项时使用 `requestAnimationFrame` 或 Worker 分片以保持 UI 响应
  - 对清理/删除操作提供确认与事务性回退（尽可能）以防误删
 -->
<script setup lang="ts">
import { ref, reactive } from 'vue'
import {
  NCard, NGrid, NGridItem, NProgress, NButton,
  NSpace, NTag, NEmpty, NSpin, NAlert
} from 'naive-ui'
import { RefreshOutline, TrashOutline } from '@vicons/ionicons5'

import { getAllStorageStats, getBrowserStorageInfo, getStorageStats, getMetadata, getCache, clearStorage, type StorageStats, type BrowserStorageInfo } from '@/composables/useCache'
import { POEM_INDEX_STORAGE, POEMS_STORAGE, AUTHORS_STORAGE, WORDCOUNT_STORAGE } from '@/composables/useMetadataLoader'
import { useKeywordIndex } from '@/composables/useKeywordIndex'

// 诗词数据存储键
const POEMS_SUMMARY_STORAGE = 'poems-summary-v2'
const POEMS_DETAIL_STORAGE = 'poems-detail-v2'

const props = defineProps<{
  isLoadingStats?: boolean
}>()

// 使用 props 避免未使用警告
if (props.isLoadingStats) {
  console.log('Loading stats from parent...')
}

const isLoading = ref(false)
const loadingStep = ref('')
const loadProgress = ref(0)

const loadingState = reactive({
  browserInfo: false,
  searchIndex: false,
  keywordIndex: false,
  storageStats: false
})

const storageStats = ref<StorageStats[]>([])
const browserStorageInfo = ref<BrowserStorageInfo | null>(null)
const selectedStorage = ref<string>('')
const selectedStorageDetail = ref<StorageStats | null>(null)

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

const isClearing = ref(false)
const clearMessage = ref('')

// 使用 requestAnimationFrame 替代 delay，让 UI 有机会更新
const yieldToMain = () => new Promise(resolve => requestAnimationFrame(resolve))

const updateProgress = async (step: string, stateKey: keyof typeof loadingState, progress: number) => {
  loadingStep.value = step
  loadingState[stateKey] = true
  loadProgress.value = progress
  // 只在高进度时让出主线程，减少不必要的延迟
  if (progress % 20 === 0) {
    await yieldToMain()
  }
}

const resetLoadingState = () => {
  loadingState.browserInfo = false
  loadingState.searchIndex = false
  loadingState.keywordIndex = false
  loadingState.storageStats = false
}

const loadStorageDetails = async () => {
  resetLoadingState()
  
  isLoading.value = true
  loadProgress.value = 0
  loadingStep.value = '正在初始化...'
  
  try {
    // 并行获取基础信息
    loadingStep.value = '正在获取浏览器存储信息...'
    const [allStats, browserInfo] = await Promise.all([
      getAllStorageStats(),
      getBrowserStorageInfo()
    ])
    storageStats.value = allStats
    browserStorageInfo.value = browserInfo
    await updateProgress('词频相似度数据加载中...', 'browserInfo', 20)
  } catch (e) {
    console.error('Failed to load storage details:', e)
  }

  try {
    loadingStep.value = '正在加载搜索索引...'
    const { usePoemIndexManifest } = await import('@/composables/useMetadataLoader')
    const piMeta = usePoemIndexManifest()

    // 并行加载搜索索引
    const [searchIndexMetaData, searchIndexPrefixes] = await Promise.all([
      piMeta.loadMetadata(),
      getCache<string[]>(POEM_INDEX_STORAGE, 'loaded-prefixes')
    ])
    
    searchIndexStats.value.totalPrefixes = Object.keys(searchIndexMetaData?.prefixMap || {}).length
    
    if (searchIndexPrefixes) {
      searchIndexStats.value.cachedPrefixes = searchIndexPrefixes.length
      searchIndexStats.value.loaded = true
    }
    
    await updateProgress('关键词索引加载中...', 'searchIndex', 70)

    // 加载关键词索引 - 使用 computed 属性
    keywordIndexStats.value.totalChunks = keywordIndex.totalChunks.value
    keywordIndexStats.value.cachedChunks = keywordIndex.loadedChunkIds.value.length
    keywordIndexStats.value.loaded = keywordIndexStats.value.cachedChunks > 0
    
    await updateProgress('计算存储统计...', 'keywordIndex', 85)

    // 最后刷新存储统计
    storageStats.value = await getAllStorageStats()
    loadingState.storageStats = true
    loadProgress.value = 100
    
    loadingStep.value = '加载完成'
  } catch (e) {
    console.error('Failed to load metadata:', e)
    loadingStep.value = '加载失败'
  } finally {
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

const handleClearCache = async () => {
  isClearing.value = true
  clearMessage.value = '正在清空缓存...'

  try {
    // 并行清空所有缓存
    await Promise.all([
      clearStorage(POEMS_STORAGE),
      clearStorage(POEMS_SUMMARY_STORAGE),
      clearStorage(POEMS_DETAIL_STORAGE),
      clearStorage(AUTHORS_STORAGE),
      clearStorage(WORDCOUNT_STORAGE),
      clearStorage(POEM_INDEX_STORAGE),
      clearStorage(keywordIndex.storageName)
    ])
    
    clearMessage.value = '缓存已清空'
    await loadStorageDetails()
    clearMessage.value = ''
  } catch (e) {
    console.error('清空缓存失败:', e)
    clearMessage.value = '清空失败'
  } finally {
    isClearing.value = false
  }
}
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
            <div class="loading-state-item" :class="{ done: loadingState.searchIndex }">
              <span class="state-icon">{{ loadingState.searchIndex ? '✓' : '○' }}</span>
              搜索索引
            </div>
            <div class="loading-state-item" :class="{ done: loadingState.keywordIndex }">
              <span class="state-icon">{{ loadingState.keywordIndex ? '✓' : '○' }}</span>
              关键词索引
            </div>
            <div class="loading-state-item" :class="{ done: loadingState.storageStats }">
              <span class="state-icon">{{ loadingState.storageStats ? '✓' : '○' }}</span>
              存储统计
            </div>
          </div>
        </div>
      </NCard>
    </div>

    <NAlert v-if="clearMessage" :type="clearMessage === '清空失败' ? 'error' : 'success'" class="mb-4">
      {{ clearMessage }}
    </NAlert>

    <NGrid :cols="2" :x-gap="16" :y-gap="16" class="mb-4">
      <NGridItem>
        <NCard title="浏览器存储">
          <div v-if="browserStorageInfo && browserStorageInfo.quota" class="storage-info">
            <div class="info-row">
          <span class="info-label">已用:</span>
          <span class="info-value">{{ formatBytes(browserStorageInfo.quota.usage) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">限额:</span>
          <span class="info-value">{{ formatBytes(browserStorageInfo.quota.quota) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">使用率:</span>
          <span class="info-value">{{ Math.round((browserStorageInfo.quota.usage / browserStorageInfo.quota.quota) * 100) }}%</span>
        </div>
            <NProgress
              type="line"
              :percentage="Math.round((browserStorageInfo.quota.usage / browserStorageInfo.quota.quota) * 100)"
              :indicator-placement="'inside'"
              :status="Math.round((browserStorageInfo.quota.usage / browserStorageInfo.quota.quota) * 100) > 90 ? 'error' : Math.round((browserStorageInfo.quota.usage / browserStorageInfo.quota.quota) * 100) > 70 ? 'warning' : 'success'"
            />
          </div>
          <NEmpty v-else description="暂无数据" />
        </NCard>
      </NGridItem>

      <NGridItem>
        <NCard title="数据概览">
          <NSpace vertical>
            <div class="stat-row">
              <NTag type="info">搜索索引</NTag>
              <span v-if="searchIndexStats.loaded">
                项数: {{ searchIndexStats.cachedPrefixes.toLocaleString() }}
              </span>
              <span v-else>未加载</span>
            </div>
            <div class="stat-row">
              <NTag type="warning">关键词索引</NTag>
              <span v-if="keywordIndexStats.loaded">
                分块: {{ keywordIndexStats.cachedChunks }}/{{ keywordIndexStats.totalChunks }}
              </span>
              <span v-else>未加载</span>
            </div>
          </NSpace>
        </NCard>
      </NGridItem>
    </NGrid>

    <NCard title="存储详情" class="mb-4">
      <NGrid :cols="3" :x-gap="12" :y-gap="12">
        <NGridItem v-for="stat in storageStats" :key="stat.storage">
          <NCard
            :class="['storage-item', { active: selectedStorage === stat.storage }]"
            @click="viewStorageDetail(stat.storage)"
            hoverable
          >
            <div class="storage-name">{{ stat.storage }}</div>
            <div class="storage-size">{{ formatBytes(stat.totalSize) }}</div>
            <div class="storage-count">{{ stat.chunkCount + stat.cacheCount }} 项</div>
          </NCard>
        </NGridItem>
      </NGrid>
    </NCard>

    <NCard v-if="selectedStorageDetail" :title="`存储详情: ${selectedStorageDetail.storage}`" class="mb-4">
      <div class="detail-info">
        <div class="detail-row">
          <span class="detail-label">名称:</span>
          <span class="detail-value">{{ selectedStorageDetail.storage }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">大小:</span>
          <span class="detail-value">{{ formatBytes(selectedStorageDetail.totalSize) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">条目:</span>
          <span class="detail-value">{{ selectedStorageDetail.chunkCount + selectedStorageDetail.cacheCount }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">块数:</span>
          <span class="detail-value">{{ selectedStorageDetail.chunkCount }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">缓存数:</span>
          <span class="detail-value">{{ selectedStorageDetail.cacheCount }}</span>
        </div>
      </div>
    </NCard>

    <NSpace>
      <NButton @click="loadStorageDetails" :loading="isLoading">
        <template #icon>
          <RefreshOutline />
        </template>
        刷新
      </NButton>
      <NButton @click="handleClearCache" :loading="isClearing" type="error">
        <template #icon>
          <TrashOutline />
        </template>
        清空缓存
      </NButton>
    </NSpace>
  </div>
</template>

<style scoped>
.storage-view {
  padding: 16px;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-card {
  width: 400px;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-progress {
  width: 100%;
}

.loading-step {
  font-size: 14px;
  color: #666;
}

.loading-states {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.loading-state-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #999;
  transition: color 0.3s;
}

.loading-state-item.done {
  color: #18a058;
}

.state-icon {
  width: 16px;
  text-align: center;
}

.storage-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  color: #666;
}

.info-value {
  font-weight: 500;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-row:last-child {
  border-bottom: none;
}

.storage-item {
  cursor: pointer;
  transition: all 0.3s;
}

.storage-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.storage-item.active {
  border-color: #18a058;
  background: #f6ffed;
}

.storage-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.storage-size {
  font-size: 12px;
  color: #666;
}

.storage-count {
  font-size: 12px;
  color: #999;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  color: #666;
}

.detail-value {
  font-weight: 500;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
