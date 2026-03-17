<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline } from '@vicons/ionicons5'
import { useSearchIndexV2 } from '@/composables/useSearchIndexV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { usePoemIndexManifest, POEM_INDEX_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata } from '@/composables/useCacheV2'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'
import type { PoemSummary } from '@/composables/types'

const emit = defineEmits<{
  downloaded: []
}>()

const searchIndexV2 = useSearchIndexV2()
const poemIndexMeta = usePoemIndexManifest()
const chunkLoader = useChunkLoader()

const totalPrefixes = ref(0)
const cachedPrefixes = ref<string[]>([])
const isLoadingStats = ref(false)

const cachedCount = computed(() => cachedPrefixes.value.length)
const isFullyDownloaded = computed(() => cachedCount.value === totalPrefixes.value && totalPrefixes.value > 0)
const progressPercentage = computed(() => 
  totalPrefixes.value > 0 ? Math.round((cachedCount.value / totalPrefixes.value) * 100) : 0
)

const loadingHint = computed(() => {
  const loaded = cachedCount.value
  if (loaded === 0) return '🚀 准备下载...'
  if (isFullyDownloaded.value) return '✅ 搜索索引已准备就绪'
  return `🔍 正在下载 ${loaded.toLocaleString()} / ${totalPrefixes.value} 个前缀分块...`
})

const loadStats = async () => {
  isLoadingStats.value = true
  try {
    const manifest = await poemIndexMeta.loadMetadata()
    const prefixes = Object.keys(manifest?.prefixMap || {})
    totalPrefixes.value = prefixes.length

    const meta = await getMetadata(POEM_INDEX_STORAGE)
    if (meta && meta.loadedChunkIds) {
      cachedPrefixes.value = meta.loadedChunkIds.map(String)
    }
  } finally {
    isLoadingStats.value = false
  }
}

const downloadAll = async () => {
  try {
    const manifest = await poemIndexMeta.loadMetadata()
    const prefixes = Object.keys(manifest?.prefixMap || {})
    totalPrefixes.value = prefixes.length

    const unloadedPrefixes = prefixes.filter(p => !cachedPrefixes.value.includes(p))

    if (unloadedPrefixes.length === 0) {
      return
    }

    // 将前缀映射为索引，因为 loadChunks 只接受 number[]
    const prefixToIndex = new Map(prefixes.map((p, i) => [p, i]))
    const unloadedIndices = unloadedPrefixes.map(p => prefixToIndex.get(p)!).filter((i): i is number => i !== undefined)

    await chunkLoader.loadChunks<string>(unloadedIndices, async (index: number) => {
      const prefix = prefixes[index]!
      await searchIndexV2.loadPoemChunk(prefix)
      return prefix
    }, {
      chunkDelay: 50,
      onChunkLoaded: (_, prefix) => {
        const prefixStr = String(prefix)
        if (!cachedPrefixes.value.includes(prefixStr)) {
          cachedPrefixes.value.push(prefixStr)
        }
      },
      onComplete: () => {
        emit('downloaded')
      }
    })
  } catch (e) {
    console.error('下载失败:', e)
  }
}

onMounted(() => {
  loadStats()
})

defineExpose({
  loadStats,
  cachedCount,
  totalPrefixes
})
</script>

<template>
  <NCard title="🔍 搜索索引数据" class="download-section">
    <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
      搜索索引包含 {{ totalPrefixes }} 个前缀分块的诗词数据，支持离线搜索。
    </NAlert>

    <NProgress
      type="line"
      :percentage="progressPercentage"
      :indicator-placement="'inside'"
      :status="isFullyDownloaded ? 'success' : 'default'"
      style="margin-bottom: 16px;"
    />

    <ChunkLoaderStatus
      v-if="chunkLoader.isLoading.value || cachedCount > 0"
      :is-loading="chunkLoader.isLoading.value"
      :is-paused="chunkLoader.isPaused.value"
      :progress="Math.round((cachedCount / (totalPrefixes || 1)) * 100)"
      :loaded-count="cachedCount"
      :total-count="totalPrefixes"
      title="下载搜索索引"
      :hint="loadingHint"
      :stats="[
        { label: '已缓存前缀', value: cachedCount.toLocaleString() },
        { label: '总前缀数', value: totalPrefixes.toLocaleString() }
      ]"
      @pause="chunkLoader.pause"
      @resume="chunkLoader.resume"
      style="margin-bottom: 16px;"
    />

    <NSpace align="center" justify="space-between">
      <NSpace>
        <NTag v-if="isFullyDownloaded" type="success">
          <template #icon>
            <CheckmarkOutline />
          </template>
          已全部下载
        </NTag>
        <NTag v-else type="default">
          已下载 {{ cachedCount }} / {{ totalPrefixes }} 前缀
        </NTag>
      </NSpace>

      <NButton
        type="primary"
        size="large"
        :loading="chunkLoader.isLoading.value"
        :disabled="chunkLoader.isLoading.value || isFullyDownloaded"
        @click="downloadAll"
      >
        <template #icon>
          <DownloadOutline />
        </template>
        {{ isFullyDownloaded ? '下载完成' : '下载全部搜索索引' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
