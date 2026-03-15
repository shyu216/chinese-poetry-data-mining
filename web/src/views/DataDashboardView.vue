<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NCard, NGrid, NGridItem, NStatistic, NButton, NProgress,
  NSpace, NTag, NAlert, NTabs, NTabPane, NDataTable,
  NEmpty, NSpin, NDivider, NTimeline, NTimelineItem,
  NDescriptions, NDescriptionsItem, NNumberAnimation
} from 'naive-ui'
import {
  BookOutline, PersonOutline, CubeOutline, HardwareChipOutline,
  DownloadOutline, TrashOutline, CheckmarkCircleOutline,
  CloudDownloadOutline, StorageOutline, SpeedometerOutline
} from '@vicons/ionicons5'
import { useAuthors } from '@/composables/useAuthors'
import { 
  getCacheStats, 
  getCacheDetails, 
  clearCache,
  getCachedAuthors,
  cacheAuthors,
  clearAuthorsCache
} from '@/composables/usePoemCache'
import * as d3 from 'd3'

// Tabs
const activeTab = ref('overview')

// Stats
const poemStats = ref({
  chunks: 0,
  chunkDetails: 0,
  hasIndex: false,
  loadedChunkIds: 0,
  totalSize: 0
})

const authorStats = ref({
  cached: false,
  count: 0,
  totalSize: 0
})

const isLoadingStats = ref(false)

// Download states
const isDownloadingPoems = ref(false)
const poemDownloadProgress = ref(0)
const poemDownloadStatus = ref('')

const isDownloadingAuthors = ref(false)
const authorDownloadProgress = ref(0)
const authorDownloadStatus = ref('')

// Load stats
const loadStats = async () => {
  isLoadingStats.value = true
  try {
    const stats = await getCacheStats()
    const details = await getCacheDetails()
    poemStats.value = { ...stats, totalSize: details.totalSize }
    
    // Check authors cache
    const cachedAuthors = await getCachedAuthors()
    if (cachedAuthors) {
      authorStats.value = {
        cached: true,
        count: cachedAuthors.length,
        totalSize: JSON.stringify(cachedAuthors).length * 2
      }
    }
  } finally {
    isLoadingStats.value = false
  }
}

// Format bytes
const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Download all poem chunks
const downloadAllPoemChunks = async () => {
  isDownloadingPoems.value = true
  poemDownloadProgress.value = 0
  poemDownloadStatus.value = '正在加载索引...'
  
  try {
    // Load index first
    const indexResponse = await fetch('/data/index.json')
    const index = await indexResponse.json()
    const totalChunks = index.metadata.chunks
    
    for (let i = 0; i < totalChunks; i++) {
      poemDownloadStatus.value = `正在下载分块 ${i + 1}/${totalChunks}...`
      
      // Load chunk
      const chunkId = i.toString().padStart(4, '0')
      const response = await fetch(`/data/preprocessed/poems_chunk_${chunkId}.csv`)
      if (response.ok) {
        const text = await response.text()
        // Parse and cache
        const lines = text.split('\n').filter(line => line.trim())
        const poems = lines.slice(1).map(line => {
          const parts = line.split(',')
          return {
            id: parts[0] || '',
            title: parts[1] || '',
            author: parts[2] || '',
            dynasty: parts[3] || ''
          }
        }).filter(p => p.id)
        
        const { cacheChunkSummaries } = await import('@/composables/usePoemCache')
        await cacheChunkSummaries(i, poems)
      }
      
      poemDownloadProgress.value = Math.round(((i + 1) / totalChunks) * 100)
    }
    
    poemDownloadStatus.value = '下载完成！'
    await loadStats()
  } catch (e) {
    poemDownloadStatus.value = '下载失败: ' + (e as Error).message
  } finally {
    isDownloadingPoems.value = false
  }
}

// Download all authors
const downloadAllAuthors = async () => {
  isDownloadingAuthors.value = true
  authorDownloadProgress.value = 0
  authorDownloadStatus.value = '正在加载诗人数据...'
  
  try {
    const { loadAllAuthors } = useAuthors()
    const authors = await loadAllAuthors()
    
    // Cache authors
    await cacheAuthors(authors)
    
    authorDownloadProgress.value = 100
    authorDownloadStatus.value = '下载完成！'
    await loadStats()
  } catch (e) {
    authorDownloadStatus.value = '下载失败: ' + (e as Error).message
  } finally {
    isDownloadingAuthors.value = false
  }
}

// Clear cache
const handleClearCache = async () => {
  await clearCache()
  await clearAuthorsCache()
  await loadStats()
}

// Table columns for chunks
const chunkColumns = [
  { title: '分块ID', key: 'id', width: 100 },
  { title: '诗词数量', key: 'count', width: 120 },
  { title: '缓存时间', key: 'time', width: 180 }
]

const chunkData = ref<any[]>([])

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="data-dashboard">
    <header class="page-header">
      <h1 class="page-title">
        <StorageOutline class="title-icon" />
        数据管理中心
      </h1>
      <p class="page-subtitle">
        管理本地缓存数据，支持离线浏览
      </p>
    </header>

    <NTabs v-model:value="activeTab" type="line" size="large" class="dashboard-tabs">
      <!-- Overview Tab -->
      <NTabPane name="overview" tab="总览">
        <NSpin :show="isLoadingStats">
          <NSpace vertical size="large">
            <!-- Overall Stats -->
            <NGrid :cols="4" :x-gap="16" :y-gap="16">
              <NGridItem>
                <NCard class="stat-card">
                  <NStatistic label="诗词分块">
                    <template #prefix>
                      <CubeOutline style="color: #8b2635; font-size: 24px;" />
                    </template>
                    <NNumberAnimation :from="0" :to="poemStats.chunks" />
                    <template #suffix>
                      <span style="font-size: 14px; color: #999;">/ 333</span>
                    </template>
                  </NStatistic>
                </NCard>
              </NGridItem>
              <NGridItem>
                <NCard class="stat-card">
                  <NStatistic label="诗人数据">
                    <template #prefix>
                      <PersonOutline style="color: #8b2635; font-size: 24px;" />
                    </template>
                    <NNumberAnimation :from="0" :to="authorStats.count" />
                    <template #suffix>
                      <span style="font-size: 14px; color: #999;">/ 857</span>
                    </template>
                  </NStatistic>
                </NCard>
              </NGridItem>
              <NGridItem>
                <NCard class="stat-card">
                  <NStatistic label="缓存索引">
                    <template #prefix>
                      <BookOutline style="color: #8b2635; font-size: 24px;" />
                    </template>
                    <NTag :type="poemStats.hasIndex ? 'success' : 'default'" size="small">
                      {{ poemStats.hasIndex ? '已缓存' : '未缓存' }}
                    </NTag>
                  </NStatistic>
                </NCard>
              </NGridItem>
              <NGridItem>
                <NCard class="stat-card">
                  <NStatistic label="总缓存大小">
                    <template #prefix>
                      <HardwareChipOutline style="color: #8b2635; font-size: 24px;" />
                    </template>
                    {{ formatBytes(poemStats.totalSize + authorStats.totalSize) }}
                  </NStatistic>
                </NCard>
              </NGridItem>
            </NGrid>

            <!-- Storage Visualization -->
            <NCard title="存储分布" class="storage-viz">
              <NGrid :cols="2" :x-gap="24">
                <NGridItem>
                  <div class="storage-item">
                    <div class="storage-header">
                      <BookOutline style="color: #8b2635;" />
                      <span>诗词数据</span>
                      <NTag type="success" size="small">{{ poemStats.chunks }} 分块</NTag>
                    </div>
                    <NProgress
                      type="line"
                      :percentage="Math.round(poemStats.chunks / 333 * 100)"
                      :indicator-placement="'inside'"
                      status="success"
                      :height="20"
                    />
                    <div class="storage-size">{{ formatBytes(poemStats.totalSize) }}</div>
                  </div>
                </NGridItem>
                <NGridItem>
                  <div class="storage-item">
                    <div class="storage-header">
                      <PersonOutline style="color: #8b2635;" />
                      <span>诗人数据</span>
                      <NTag :type="authorStats.cached ? 'success' : 'default'" size="small">
                        {{ authorStats.cached ? '已缓存' : '未缓存' }}
                      </NTag>
                    </div>
                    <NProgress
                      type="line"
                      :percentage="authorStats.cached ? 100 : 0"
                      :indicator-placement="'inside'"
                      :status="authorStats.cached ? 'success' : 'default'"
                      :height="20"
                    />
                    <div class="storage-size">{{ formatBytes(authorStats.totalSize) }}</div>
                  </div>
                </NGridItem>
              </NGrid>
            </NCard>

            <!-- Quick Actions -->
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
              </NSpace>
            </NCard>
          </NSpace>
        </NSpin>
      </NTabPane>

      <!-- Download Tab -->
      <NTabPane name="download" tab="数据下载">
        <NSpace vertical size="large">
          <!-- Poems Download -->
          <NCard title="📚 诗词数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              诗词数据库包含 333 个分块，约 332,712 首诗词。下载后可离线浏览，无需重复加载。
            </NAlert>
            
            <div class="download-status">
              <div class="status-item">
                <span class="status-label">当前缓存:</span>
                <NTag :type="poemStats.chunks > 0 ? 'success' : 'default'">
                  {{ poemStats.chunks }}/333 分块
                </NTag>
                <span class="status-size">{{ formatBytes(poemStats.totalSize) }}</span>
              </div>
            </div>

            <NButton
              type="primary"
              size="large"
              :loading="isDownloadingPoems"
              :disabled="isDownloadingPoems || poemStats.chunks === 333"
              @click="downloadAllPoemChunks"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ isDownloadingPoems ? poemDownloadStatus : (poemStats.chunks === 333 ? '已全部下载' : '下载全部诗词数据') }}
            </NButton>
            
            <NProgress
              v-if="isDownloadingPoems"
              type="line"
              :percentage="poemDownloadProgress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>

          <!-- Authors Download -->
          <NCard title="👥 诗人数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              诗人数据库包含 857 位诗人的统计信息，包括诗词数量、诗体分布等。约 51MB。
            </NAlert>
            
            <div class="download-status">
              <div class="status-item">
                <span class="status-label">当前缓存:</span>
                <NTag :type="authorStats.cached ? 'success' : 'default'">
                  {{ authorStats.cached ? '已缓存' : '未缓存' }}
                </NTag>
                <span class="status-size">{{ formatBytes(authorStats.totalSize) }}</span>
              </div>
            </div>

            <NButton
              type="primary"
              size="large"
              :loading="isDownloadingAuthors"
              :disabled="isDownloadingAuthors || authorStats.cached"
              @click="downloadAllAuthors"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ isDownloadingAuthors ? authorDownloadStatus : (authorStats.cached ? '已下载' : '下载全部诗人数据') }}
            </NButton>
            
            <NProgress
              v-if="isDownloadingAuthors"
              type="line"
              :percentage="authorDownloadProgress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>
        </NSpace>
      </NTabPane>

      <!-- Cache Details Tab -->
      <NTabPane name="details" tab="缓存详情">
        <NCard title="诗词分块缓存">
          <NEmpty v-if="poemStats.chunks === 0" description="暂无缓存数据" />
          <div v-else>
            <p style="margin-bottom: 16px; color: #666;">
              已缓存 {{ poemStats.chunks }} 个分块，共 {{ formatBytes(poemStats.totalSize) }}
            </p>
            <!-- Chunk list would go here -->
          </div>
        </NCard>
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.data-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
  color: #8b2635;
}

.page-subtitle {
  font-size: 16px;
  color: #666;
}

.dashboard-tabs {
  margin-top: 24px;
}

.stat-card {
  text-align: center;
}

.stat-card :deep(.n-statistic__label) {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-card :deep(.n-statistic__value) {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
}

.storage-viz {
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
}

.storage-item {
  padding: 16px;
}

.storage-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 500;
}

.storage-size {
  text-align: right;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.download-card {
  transition: all 0.3s ease;
}

.download-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.download-status {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-label {
  font-size: 14px;
  color: #666;
}

.status-size {
  margin-left: auto;
  font-size: 14px;
  color: #999;
}
</style>
