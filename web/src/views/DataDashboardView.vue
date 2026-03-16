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
  CloudDownloadOutline, ServerOutline, SpeedometerOutline,
  GitNetworkOutline
} from '@vicons/ionicons5'
import { useAuthors, loadAuthorsMeta } from '@/composables/useAuthors'
import { useWordSimilarity } from '@/composables/useWordSimilarity'
import {
  getCacheStats,
  getCacheDetails,
  clearCache,
  getCachedAuthors,
  cacheAuthors,
  clearAuthorsCache,
  getWordSimilarityCacheDetails,
  clearWordSimilarityCache,
  getAllCachedAuthorChunks,
  getCachedAuthorChunkIds
} from '@/composables/usePoemCache'
import * as d3 from 'd3'

// Authors meta info
const authorsMetaTotal = ref(0)

// Word Similarity meta info
const wordSimMeta = ref({
  totalChunks: 231,
  vocabSize: 88227
})

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

const wordSimStats = ref({
  vocabCached: false,
  vocabSize: 0,
  chunks: 0,
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

const isDownloadingWordSim = ref(false)
const wordSimDownloadProgress = ref(0)
const wordSimDownloadStatus = ref('')

// Load stats
const loadStats = async () => {
  isLoadingStats.value = true
  try {
    const stats = await getCacheStats()
    const details = await getCacheDetails()
    poemStats.value = { ...stats, totalSize: details.totalSize }

    // Update chunk data for table
    chunkData.value = details.chunks.map(c => ({
      id: c.id,
      count: c.count,
      time: new Date(c.timestamp).toLocaleString('zh-CN')
    }))

    // Load authors meta to get total count
    try {
      const meta = await loadAuthorsMeta()
      authorsMetaTotal.value = meta.totalAuthors || meta.total
    } catch {
      authorsMetaTotal.value = 0
    }

    // Check authors cache (try new chunked cache first, then fallback to old format)
    let cachedAuthors = await getAllCachedAuthorChunks()
    if (!cachedAuthors) {
      // Fallback to old format
      cachedAuthors = await getCachedAuthors()
    }
    if (cachedAuthors && cachedAuthors.length > 0) {
      authorStats.value = {
        cached: true,
        count: cachedAuthors.length,
        totalSize: JSON.stringify(cachedAuthors).length * 2
      }
    } else {
      // Check if we have partial chunked cache
      const cachedChunkIds = await getCachedAuthorChunkIds()
      if (cachedChunkIds.length > 0) {
        // We have partial cache, load it to get count
        const partialAuthors = await getAllCachedAuthorChunks()
        if (partialAuthors) {
          authorStats.value = {
            cached: true,
            count: partialAuthors.length,
            totalSize: JSON.stringify(partialAuthors).length * 2
          }
        }
      }
    }

    // Check word similarity cache
    const wordSimDetails = await getWordSimilarityCacheDetails()
    wordSimStats.value = {
      vocabCached: wordSimDetails.vocabCached,
      vocabSize: wordSimDetails.vocabSize,
      chunks: wordSimDetails.chunks.length,
      totalSize: wordSimDetails.totalSize
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

// Parse CSV line handling quoted fields
const parseCSVLine = (line: string): string[] => {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    const nextChar = line[i + 1]
    
    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // Escaped quote
        current += '"'
        i++
      } else {
        // Toggle quote state
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current)
      current = ''
    } else {
      current += char
    }
  }
  result.push(current)
  return result
}

// Download all poem chunks
const downloadAllPoemChunks = async () => {
  isDownloadingPoems.value = true
  poemDownloadProgress.value = 0
  poemDownloadStatus.value = '正在加载索引...'

  try {
    // Load index first
    const indexResponse = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/poems_chunk_meta.json`)
    if (!indexResponse.ok) {
      throw new Error('无法加载索引文件')
    }
    const index = await indexResponse.json()
    const totalChunks = index.metadata.chunks

    console.log(`[Download] Starting download of ${totalChunks} chunks`)

    for (let i = 0; i < totalChunks; i++) {
      poemDownloadStatus.value = `正在下载分块 ${i + 1}/${totalChunks}...`

      // Load chunk
      const chunkId = i.toString().padStart(4, '0')
      const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/poems_chunk_${chunkId}.csv`)

      if (response.ok) {
        const text = await response.text()
        // Parse and cache
        const lines = text.split('\n').filter(line => line.trim())
        const poems: { id: string; title: string; author: string; dynasty: string; genre: string }[] = []

        for (let j = 1; j < lines.length; j++) {
          const line = lines[j]
          if (!line) continue
          const parts = parseCSVLine(line)
          if (parts[0]) {
            poems.push({
              id: parts[0] || '',
              title: parts[1] || '',
              author: parts[2] || '',
              dynasty: parts[3] || '',
              genre: parts[4] || ''
            })
          }
        }

        const { cacheChunkSummaries } = await import('@/composables/usePoemCache')
        await cacheChunkSummaries(i, poems)
        console.log(`[Download] Chunk ${i} cached: ${poems.length} poems`)
      } else {
        console.warn(`[Download] Failed to load chunk ${i}: ${response.status}`)
      }

      poemDownloadProgress.value = Math.round(((i + 1) / totalChunks) * 100)

      // Allow UI to update every 10 chunks
      if (i % 10 === 0) {
        await new Promise(resolve => setTimeout(resolve, 0))
      }
    }

    poemDownloadStatus.value = '下载完成！'
    await loadStats()
  } catch (e) {
    console.error('[Download] Error:', e)
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
    const { loadAllAuthors, onIncrementalLoad } = useAuthors()
    
    // Subscribe to progress updates
    const unsubscribe = onIncrementalLoad((authors, progress) => {
      authorDownloadProgress.value = progress
      authorDownloadStatus.value = `已加载 ${authors.length} 位诗人...`
    })
    
    const authors = await loadAllAuthors(true)
    
    // Unsubscribe after loading
    unsubscribe()
    
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
  await clearWordSimilarityCache()
  await loadStats()
}

// Word Similarity composable instance
const wordSimilarity = useWordSimilarity()

// Download all word similarity data
const downloadAllWordSim = async () => {
  isDownloadingWordSim.value = true
  wordSimDownloadProgress.value = 0
  wordSimDownloadStatus.value = '正在加载词表...'

  try {
    // Initialize to load vocab and metadata
    await wordSimilarity.initialize()
    wordSimDownloadProgress.value = 10
    wordSimDownloadStatus.value = '词表加载完成，准备下载 chunks...'

    // 使用实际的 vocabSize 而不是硬编码的值
    const actualVocabSize = wordSimilarity.vocabSize.value
    const totalChunks = wordSimMeta.value.totalChunks
    const wordIds = Array.from({ length: actualVocabSize }, (_, i) => i)

    console.log(`[downloadAllWordSim] Actual vocab size: ${actualVocabSize}, total chunks: ${totalChunks}`)

    // Batch preload chunks
    const batchSize = 10
    const wordsPerChunk = Math.ceil(actualVocabSize / totalChunks)
    
    for (let i = 0; i < totalChunks; i += batchSize) {
      const startWordId = i * wordsPerChunk
      const endWordId = Math.min((i + batchSize) * wordsPerChunk, actualVocabSize)
      const batch = wordIds.slice(startWordId, endWordId)
      
      console.log(`[downloadAllWordSim] Loading batch ${i}-${Math.min(i + batchSize, totalChunks)}: wordIds ${startWordId}-${endWordId}`)
      
      await wordSimilarity.preloadChunks(batch)

      wordSimDownloadProgress.value = Math.round(10 + ((i + batchSize) / totalChunks * 90))
      wordSimDownloadStatus.value = `已下载 ${Math.min(i + batchSize, totalChunks)}/${totalChunks} 个分块...`
    }

    wordSimDownloadProgress.value = 100
    wordSimDownloadStatus.value = '下载完成！'
    await loadStats()
  } catch (e) {
    wordSimDownloadStatus.value = '下载失败: ' + (e as Error).message
    console.error('[downloadAllWordSim] Error:', e)
  } finally {
    isDownloadingWordSim.value = false
  }
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
        <ServerOutline class="title-icon" />
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
                      <span style="font-size: 14px; color: #999;">位</span>
                    </template>
                  </NStatistic>
                </NCard>
              </NGridItem>
              <NGridItem>
                <NCard class="stat-card">
                  <NStatistic label="相似词数据">
                    <template #prefix>
                      <GitNetworkOutline style="color: #8b2635; font-size: 24px;" />
                    </template>
                    <NTag :type="wordSimStats.vocabCached ? 'success' : 'default'" size="small">
                      {{ wordSimStats.vocabCached ? '已缓存' : '未缓存' }}
                    </NTag>
                    <template #suffix v-if="wordSimStats.vocabCached">
                      <span style="font-size: 12px; color: #999;">{{ wordSimStats.chunks }} chunks</span>
                    </template>
                  </NStatistic>
                </NCard>
              </NGridItem>
              <NGridItem>
                <NCard class="stat-card">
                  <NStatistic label="总缓存大小">
                    <template #prefix>
                      <HardwareChipOutline style="color: #8b2635; font-size: 24px;" />
                    </template>
                    {{ formatBytes(poemStats.totalSize + authorStats.totalSize + wordSimStats.totalSize) }}
                  </NStatistic>
                </NCard>
              </NGridItem>
            </NGrid>

            <!-- Storage Visualization -->
            <NCard title="存储分布" class="storage-viz">
              <NGrid :cols="3" :x-gap="24">
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
                      <NTag :type="authorStats.count > 0 ? 'success' : 'default'" size="small">
                        <template v-if="authorsMetaTotal > 0">
                          {{ authorStats.count }}/{{ authorsMetaTotal.toLocaleString() }} 位
                        </template>
                        <template v-else>
                          {{ authorStats.count > 0 ? `${authorStats.count} 位` : '未缓存' }}
                        </template>
                      </NTag>
                    </div>
                    <NProgress
                      type="line"
                      :percentage="authorsMetaTotal > 0 ? Math.round(authorStats.count / authorsMetaTotal * 100) : (authorStats.count > 0 ? 100 : 0)"
                      :indicator-placement="'inside'"
                      :status="authorStats.count > 0 ? 'success' : 'default'"
                      :height="20"
                    />
                    <div class="storage-size">{{ formatBytes(authorStats.totalSize) }}</div>
                  </div>
                </NGridItem>
                <NGridItem>
                  <div class="storage-item">
                    <div class="storage-header">
                      <GitNetworkOutline style="color: #8b2635;" />
                      <span>相似词数据</span>
                      <NTag :type="wordSimStats.vocabCached ? 'success' : 'default'" size="small">
                        {{ wordSimStats.vocabCached ? `${wordSimStats.chunks}/${wordSimMeta.totalChunks} chunks` : '未缓存' }}
                      </NTag>
                    </div>
                    <NProgress
                      type="line"
                      :percentage="wordSimStats.vocabCached ? Math.round(wordSimStats.chunks / wordSimMeta.totalChunks * 100) : 0"
                      :indicator-placement="'inside'"
                      :status="wordSimStats.vocabCached ? 'success' : 'default'"
                      :height="20"
                    />
                    <div class="storage-size">{{ formatBytes(wordSimStats.totalSize) }}</div>
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
              诗人数据库包含诗人统计信息，包括诗词数量、诗体分布等。
              <template v-if="authorsMetaTotal > 0">
                共 {{ authorsMetaTotal.toLocaleString() }} 位诗人。
              </template>
            </NAlert>

            <div class="download-status">
              <div class="status-item">
                <span class="status-label">当前缓存:</span>
                <NTag :type="authorStats.count > 0 ? 'success' : 'default'">
                  <template v-if="authorsMetaTotal > 0">
                    {{ authorStats.count }}/{{ authorsMetaTotal.toLocaleString() }} 位诗人
                  </template>
                  <template v-else>
                    {{ authorStats.count > 0 ? `${authorStats.count} 位诗人` : '未缓存' }}
                  </template>
                </NTag>
                <span class="status-size">{{ formatBytes(authorStats.totalSize) }}</span>
              </div>
            </div>

            <NButton
              type="primary"
              size="large"
              :loading="isDownloadingAuthors"
              :disabled="isDownloadingAuthors || (authorsMetaTotal > 0 && authorStats.count >= authorsMetaTotal)"
              @click="downloadAllAuthors"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ isDownloadingAuthors ? authorDownloadStatus : ((authorsMetaTotal > 0 && authorStats.count >= authorsMetaTotal) ? '已全部下载' : '下载全部诗人数据') }}
            </NButton>
            
            <NProgress
              v-if="isDownloadingAuthors || (authorsMetaTotal > 0 && authorStats.count > 0 && authorStats.count < authorsMetaTotal)"
              type="line"
              :percentage="authorsMetaTotal > 0 ? Math.round(authorStats.count / authorsMetaTotal * 100) : authorDownloadProgress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>

          <!-- Word Similarity Download -->
          <NCard title="🔗 词境探索数据" class="download-card">
            <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
              词境探索数据库包含 {{ wordSimMeta.vocabSize.toLocaleString() }} 个词汇的相似度数据，共 {{ wordSimMeta.totalChunks }} 个分块。
              下载后可离线使用词境探索功能。
            </NAlert>

            <div class="download-status">
              <div class="status-item">
                <span class="status-label">当前缓存:</span>
                <NTag :type="wordSimStats.vocabCached ? 'success' : 'default'">
                  {{ wordSimStats.vocabCached ? `${wordSimStats.chunks}/${wordSimMeta.totalChunks} 分块` : '未缓存' }}
                </NTag>
                <span class="status-size">{{ formatBytes(wordSimStats.totalSize) }}</span>
              </div>
            </div>

            <NButton
              type="primary"
              size="large"
              :loading="isDownloadingWordSim"
              :disabled="isDownloadingWordSim || (wordSimStats.vocabCached && wordSimStats.chunks >= wordSimMeta.totalChunks)"
              @click="downloadAllWordSim"
              block
            >
              <template #icon>
                <DownloadOutline />
              </template>
              {{ isDownloadingWordSim ? wordSimDownloadStatus : (wordSimStats.vocabCached && wordSimStats.chunks >= wordSimMeta.totalChunks ? '已全部下载' : '下载全部词境数据') }}
            </NButton>

            <NProgress
              v-if="isDownloadingWordSim"
              type="line"
              :percentage="wordSimDownloadProgress"
              :indicator-placement="'inside'"
              status="success"
              style="margin-top: 12px;"
            />
          </NCard>
        </NSpace>
      </NTabPane>

      <!-- Cache Details Tab -->
      <NTabPane name="details" tab="缓存详情">
        <NSpace vertical size="large">
          <!-- Poem Cache Details -->
          <NCard title="诗词分块缓存">
            <NEmpty v-if="poemStats.chunks === 0" description="暂无诗词缓存数据" />
            <div v-else>
              <p style="margin-bottom: 16px; color: #666;">
                已缓存 {{ poemStats.chunks }} 个分块，共 {{ formatBytes(poemStats.totalSize) }}
              </p>
              <NDataTable
                :columns="chunkColumns"
                :data="chunkData"
                :pagination="{ pageSize: 10 }"
                size="small"
              />
            </div>
          </NCard>

          <!-- Author Cache Details -->
          <NCard title="诗人缓存">
            <NEmpty v-if="authorStats.count === 0" description="暂无诗人缓存数据" />
            <div v-else>
              <p style="margin-bottom: 16px; color: #666;">
                已缓存 {{ authorStats.count.toLocaleString() }} 位诗人
                <template v-if="authorsMetaTotal > 0">
                  / 共 {{ authorsMetaTotal.toLocaleString() }} 位
                  ({{ Math.round(authorStats.count / authorsMetaTotal * 100) }}%)
                </template>
                ，占用 {{ formatBytes(authorStats.totalSize) }}
              </p>
              <NTag type="success" size="small">
                <template #icon>
                  <CheckmarkCircleOutline />
                </template>
                诗人数据已缓存
              </NTag>
            </div>
          </NCard>

          <!-- Word Similarity Cache Details -->
          <NCard title="相似词缓存">
            <NEmpty v-if="!wordSimStats.vocabCached" description="暂无相似词缓存数据" />
            <div v-else>
              <p style="margin-bottom: 16px; color: #666;">
                词表已缓存 ({{ wordSimStats.vocabSize.toLocaleString() }} 词)
                <br>
                已缓存 {{ wordSimStats.chunks }} / {{ wordSimMeta.totalChunks }} 个分块
                ，占用 {{ formatBytes(wordSimStats.totalSize) }}
              </p>
            </div>
          </NCard>
        </NSpace>
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

@media (max-width: 768px) {
  .data-dashboard {
    padding: 16px 0;
  }

  .page-header {
    padding: 0 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .page-subtitle {
    font-size: 14px;
  }

  .dashboard-tabs {
    padding: 0 16px;
  }

  .dashboard-tabs :deep(.n-tabs-nav) {
    overflow-x: auto;
  }

  .dashboard-tabs :deep(.n-tabs-tab) {
    padding: 8px 12px;
    font-size: 14px;
  }

  .stat-card :deep(.n-statistic__label) {
    font-size: 12px;
  }

  .stat-card :deep(.n-statistic-value) {
    font-size: 20px;
  }

  .storage-viz :deep(.n-grid) {
    grid-template-columns: 1fr !important;
  }

  .storage-viz :deep(.n-grid-item) {
    margin-bottom: 16px;
  }

  .storage-viz :deep(.n-grid-item:last-child) {
    margin-bottom: 0;
  }

  .download-card :deep(.n-button) {
    font-size: 14px;
  }

  .download-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .status-item {
    width: 100%;
  }
}
</style>
