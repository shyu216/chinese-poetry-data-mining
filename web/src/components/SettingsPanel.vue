<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  NDrawer, NDrawerContent, NCard, NButton, NProgress,
  NSpace, NTag, NDivider, NSpin, NAlert, NStatistic,
  NGrid, NGridItem
} from 'naive-ui'
import {
  SettingsOutline, DownloadOutline, TrashOutline,
  ServerOutline, HardwareChipOutline, CubeOutline
} from '@vicons/ionicons5'
import { getCacheStats, getCacheDetails, clearCache } from '@/composables/usePoemCache'
import { usePoems } from '@/composables/usePoems'
import * as d3 from 'd3'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { loadChunkSummaries, loadIndex } = usePoems()

// Stats
const stats = ref({
  chunks: 0,
  chunkDetails: 0,
  hasIndex: false,
  loadedChunkIds: 0
})

const cacheDetails = ref<{
  chunks: { id: number; count: number; timestamp: number }[]
  totalSize: number
}>({ chunks: [], totalSize: 0 })

const isLoading = ref(false)
const isDownloading = ref(false)
const downloadProgress = ref(0)
const downloadStatus = ref('')

// Format bytes
const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Format date
const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// Load stats
const loadStats = async () => {
  isLoading.value = true
  try {
    stats.value = await getCacheStats()
    cacheDetails.value = await getCacheDetails()
    renderChart()
  } finally {
    isLoading.value = false
  }
}

// Download all chunks
const downloadAllChunks = async () => {
  isDownloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = '正在加载索引...'
  
  try {
    const index = await loadIndex()
    const totalChunks = index.metadata.chunks
    
    for (let i = 0; i < totalChunks; i++) {
      downloadStatus.value = `正在下载分块 ${i + 1}/${totalChunks}...`
      await loadChunkSummaries(i)
      downloadProgress.value = Math.round(((i + 1) / totalChunks) * 100)
    }
    
    downloadStatus.value = '下载完成！'
    await loadStats()
  } catch (e) {
    downloadStatus.value = '下载失败: ' + (e as Error).message
  } finally {
    isDownloading.value = false
  }
}

// Clear cache
const handleClearCache = async () => {
  await clearCache()
  await loadStats()
}

// D3 Chart
const chartRef = ref<HTMLElement | null>(null)

const renderChart = () => {
  if (!chartRef.value || cacheDetails.value.chunks.length === 0) return
  
  const container = chartRef.value
  container.innerHTML = ''
  
  const margin = { top: 20, right: 20, bottom: 40, left: 60 }
  const width = container.clientWidth - margin.left - margin.right
  const height = 200 - margin.top - margin.bottom
  
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)
  
  // X scale
  const x = d3.scaleBand()
    .domain(cacheDetails.value.chunks.map(d => d.id.toString()))
    .range([0, width])
    .padding(0.1)
  
  // Y scale
  const y = d3.scaleLinear()
    .domain([0, d3.max(cacheDetails.value.chunks, d => d.count) || 0])
    .range([height, 0])
  
  // Bars
  svg.selectAll('.bar')
    .data(cacheDetails.value.chunks)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', d => x(d.id.toString()) || 0)
    .attr('width', x.bandwidth())
    .attr('y', d => y(d.count))
    .attr('height', d => height - y(d.count))
    .attr('fill', '#8b2635')
    .attr('rx', 2)
    .on('mouseover', function() {
      d3.select(this).attr('fill', '#a03040')
    })
    .on('mouseout', function() {
      d3.select(this).attr('fill', '#8b2635')
    })
  
  // X axis
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).tickValues(x.domain().filter((_, i) => i % 20 === 0)))
    .style('font-size', '10px')
  
  // Y axis
  svg.append('g')
    .call(d3.axisLeft(y).ticks(5))
    .style('font-size', '10px')
  
  // Labels
  svg.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', 0 - margin.left)
    .attr('x', 0 - (height / 2))
    .attr('dy', '1em')
    .style('text-anchor', 'middle')
    .style('font-size', '12px')
    .style('fill', '#666')
    .text('诗词数量')
  
  svg.append('text')
    .attr('transform', `translate(${width / 2}, ${height + margin.bottom - 5})`)
    .style('text-anchor', 'middle')
    .style('font-size', '12px')
    .style('fill', '#666')
    .text('分块 ID')
}

onMounted(() => {
  loadStats()
})

// Chunk distribution data
const chunkDistribution = computed(() => {
  const ranges = [
    { label: '0-50', min: 0, max: 50, count: 0 },
    { label: '51-100', min: 51, max: 100, count: 0 },
    { label: '101-150', min: 101, max: 150, count: 0 },
    { label: '151-200', min: 151, max: 200, count: 0 },
    { label: '201-250', min: 201, max: 250, count: 0 },
    { label: '251-333', min: 251, max: 333, count: 0 }
  ]
  
  cacheDetails.value.chunks.forEach(chunk => {
    const range = ranges.find(r => chunk.id >= r.min && chunk.id <= r.max)
    if (range) range.count++
  })
  
  return ranges
})
</script>

<template>
  <NDrawer
    :show="show"
    @update:show="emit('update:show', $event)"
    placement="left"
    width="500"
  >
    <NDrawerContent title="数据管理" closable>
      <NSpin :show="isLoading">
        <NSpace vertical size="large">
          <!-- Overview Cards -->
          <NGrid :cols="2" :x-gap="12">
            <NGridItem>
              <NCard>
                <NStatistic label="已缓存分块" :value="stats.chunks">
                  <template #prefix>
                    <CubeOutline style="font-size: 18px; color: #8b2635;" />
                  </template>
                </NStatistic>
              </NCard>
            </NGridItem>
            <NGridItem>
              <NCard>
                <NStatistic label="缓存大小" :value="formatBytes(cacheDetails.totalSize)">
                  <template #prefix>
                    <HardwareChipOutline style="font-size: 18px; color: #8b2635;" />
                  </template>
                </NStatistic>
              </NCard>
            </NGridItem>
          </NGrid>

          <!-- Data Download Section -->
          <NCard title="📥 数据下载" bordered>
            <NSpace vertical>
              <NAlert type="info" :show-icon="false">
                诗词数据库包含 333 个分块，约 332,712 首诗词。
                下载后可离线浏览，无需重复加载。
              </NAlert>
              
              <NButton
                type="primary"
                size="large"
                :loading="isDownloading"
                :disabled="isDownloading"
                @click="downloadAllChunks"
                block
              >
                <template #icon>
                  <DownloadOutline />
                </template>
                {{ isDownloading ? downloadStatus : '下载全部诗词数据' }}
              </NButton>
              
              <NProgress
                v-if="isDownloading"
                type="line"
                :percentage="downloadProgress"
                :indicator-placement="'inside'"
                status="success"
              />
              
              <NSpace v-if="stats.chunks > 0">
                <NTag type="success">已下载 {{ stats.chunks }}/333 分块</NTag>
                <NTag type="info">{{ formatBytes(cacheDetails.totalSize) }}</NTag>
              </NSpace>
            </NSpace>
          </NCard>

          <!-- Visualization Section -->
          <NCard title="📊 缓存可视化" bordered v-if="cacheDetails.chunks.length > 0">
            <NSpace vertical>
              <div ref="chartRef" class="chart-container"></div>
              
              <NDivider />
              
              <div class="distribution-grid">
                <div
                  v-for="range in chunkDistribution"
                  :key="range.label"
                  class="distribution-item"
                >
                  <span class="range-label">{{ range.label }}</span>
                  <NProgress
                    type="line"
                    :percentage="Math.round(range.count / 50 * 100)"
                    :show-indicator="false"
                    status="success"
                    :height="8"
                  />
                  <span class="range-count">{{ range.count }} 块</span>
                </div>
              </div>
            </NSpace>
          </NCard>

          <!-- Cache Management -->
          <NCard title="⚙️ 缓存管理" bordered>
            <NSpace vertical>
              <div class="cache-info">
                <div class="info-row">
                  <ServerOutline />
                  <span>索引数据:</span>
                  <NTag :type="stats.hasIndex ? 'success' : 'default'" size="small">
                    {{ stats.hasIndex ? '已缓存' : '未缓存' }}
                  </NTag>
                </div>
                <div class="info-row">
                  <CubeOutline />
                  <span>分块摘要:</span>
                  <span class="value">{{ stats.chunks }} 个</span>
                </div>
                <div class="info-row">
                  <HardwareChipOutline />
                  <span>详情数据:</span>
                  <span class="value">{{ stats.chunkDetails }} 个</span>
                </div>
              </div>
              
              <NDivider />
              
              <NButton
                type="error"
                ghost
                @click="handleClearCache"
                :disabled="stats.chunks === 0 && !stats.hasIndex"
                block
              >
                <template #icon>
                  <TrashOutline />
                </template>
                清空所有缓存
              </NButton>
            </NSpace>
          </NCard>

          <!-- Recent Chunks -->
          <NCard title="🕐 最近缓存" bordered v-if="cacheDetails.chunks.length > 0">
            <NSpace vertical size="small">
              <div
                v-for="chunk in cacheDetails.chunks.slice(-5).reverse()"
                :key="chunk.id"
                class="chunk-item"
              >
                <span class="chunk-id">分块 {{ chunk.id }}</span>
                <span class="chunk-count">{{ chunk.count }} 首</span>
                <span class="chunk-time">{{ formatDate(chunk.timestamp) }}</span>
              </div>
            </NSpace>
          </NCard>
        </NSpace>
      </NSpin>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 200px;
}

.distribution-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.distribution-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.range-label {
  font-size: 12px;
  color: var(--color-ink-light);
}

.range-count {
  font-size: 11px;
  color: var(--color-ink-light);
  text-align: right;
}

.cache-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.info-row span {
  color: var(--color-ink-light);
}

.info-row .value {
  color: var(--color-ink);
  font-weight: 500;
  margin-left: auto;
}

.chunk-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--color-bg-paper);
  border-radius: 6px;
  font-size: 13px;
}

.chunk-id {
  color: var(--color-seal);
  font-weight: 500;
  min-width: 60px;
}

.chunk-count {
  color: var(--color-ink);
}

.chunk-time {
  color: var(--color-ink-light);
  font-size: 11px;
  margin-left: auto;
}
</style>
