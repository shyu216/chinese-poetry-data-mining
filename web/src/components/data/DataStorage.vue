<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NCard, NGrid, NGridItem, NProgress, NButton,
  NSpace, NTag, NTabs, NTabPane, NEmpty, NDivider
} from 'naive-ui'

import { getAllStorageStats, getBrowserStorageInfo, getStorageStats, getMetadata, type StorageStats, type BrowserStorageInfo } from '@/composables/useCacheV2'
import { WORD_SIMILARITY_STORAGE, POEM_INDEX_STORAGE } from '@/composables/useMetadataLoader'

const props = defineProps<{
  isLoadingStats?: boolean
}>()

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

const loadStorageDetails = async () => {
  try {
    storageStats.value = await getAllStorageStats()
    browserStorageInfo.value = await getBrowserStorageInfo()
  } catch (e) {
    console.error('Failed to load storage details:', e)
  }

  try {
    const { useWordSimilarityMetadata, usePoemIndexManifest } = await import('@/composables/useMetadataLoader')
    const wsMeta = useWordSimilarityMetadata()
    const piMeta = usePoemIndexManifest()

    const wordSimMetaData = await wsMeta.loadMetadata()
    wordSimStats.value.totalChunks = wordSimMetaData?.total_chunks || 0
    wordSimStats.value.vocabSize = wordSimMetaData?.vocab_size || 0

    const wordSimVocab = await getMetadata(WORD_SIMILARITY_STORAGE)
    if (wordSimVocab) {
      wordSimStats.value.vocabCached = true
    }

    const wordSimMetaStored = await getMetadata(WORD_SIMILARITY_STORAGE)
    if (wordSimMetaStored) {
      wordSimStats.value.cachedChunks = wordSimMetaStored.loadedChunkIds?.length || 0
    }

    const searchIndexMetaData = await piMeta.loadMetadata()
    searchIndexStats.value.totalPrefixes = Object.keys(searchIndexMetaData?.prefixMap || {}).length

    const searchIndexMetaStored = await getMetadata(POEM_INDEX_STORAGE)
    if (searchIndexMetaStored) {
      searchIndexStats.value.cachedPrefixes = searchIndexMetaStored.loadedChunkIds?.length || 0
      searchIndexStats.value.loaded = true
    }
  } catch (e) {
    console.error('Failed to load metadata:', e)
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
  <NSpace vertical size="large">
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
}

.storage-detail-card:hover {
  border-color: #8b2635;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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
</style>
