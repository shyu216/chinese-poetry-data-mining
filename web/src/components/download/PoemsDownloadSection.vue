<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline } from '@vicons/ionicons5'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { usePoemsMetadata, POEMS_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata } from '@/composables/useCacheV2'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'
import type { PoemSummary } from '@/composables/types'

const emit = defineEmits<{
  downloaded: []
}>()

const poemsV2 = usePoemsV2()
const poemsMeta = usePoemsMetadata()
const chunkLoader = useChunkLoader()

const totalChunks = ref(0)
const cachedChunkIds = ref<number[]>([])
const isLoadingStats = ref(false)

const cachedCount = computed(() => cachedChunkIds.value.length)
const isFullyDownloaded = computed(() => cachedCount.value === totalChunks.value && totalChunks.value > 0)
const progressPercentage = computed(() => 
  totalChunks.value > 0 ? Math.round((cachedCount.value / totalChunks.value) * 100) : 0
)

const loadingHint = computed(() => {
  const loaded = cachedCount.value
  if (loaded === 0) return '🚀 准备下载...'
  if (isFullyDownloaded.value) return '✅ 诗词数据已准备就绪'
  return `📚 正在下载 ${loaded.toLocaleString()} / ${totalChunks.value} 个分块...`
})

const loadStats = async () => {
  isLoadingStats.value = true
  try {
    const index = await poemsMeta.loadMetadata()
    totalChunks.value = index?.metadata?.chunks || 0

    const meta = await getMetadata(POEMS_STORAGE)
    if (meta) {
      cachedChunkIds.value = meta.loadedChunkIds || []
    }
  } finally {
    isLoadingStats.value = false
  }
}

const downloadAll = async () => {
  try {
    const index = await poemsMeta.loadMetadata()
    const total = index?.metadata?.chunks || 0
    totalChunks.value = total

    const allChunkIds = Array.from({ length: total }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !cachedChunkIds.value.includes(id))

    if (unloadedChunkIds.length === 0) {
      return
    }

    await chunkLoader.loadChunks<PoemSummary[]>(unloadedChunkIds, poemsV2.loadChunkSummaries, {
      chunkDelay: 50,
      onChunkLoaded: (chunkId) => {
        if (!cachedChunkIds.value.includes(chunkId)) {
          cachedChunkIds.value.push(chunkId)
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
  totalChunks
})
</script>

<template>
  <NCard title="📚 诗词数据" class="download-section">
    <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
      诗词数据库包含 {{ totalChunks }} 个分块的诗词摘要数据，支持离线浏览。
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
      :progress="Math.round((cachedCount / (totalChunks || 1)) * 100)"
      :loaded-count="cachedCount"
      :total-count="totalChunks"
      title="下载诗词数据"
      :hint="loadingHint"
      :stats="[
        { label: '已缓存分块', value: cachedCount.toLocaleString() },
        { label: '总分块数', value: totalChunks.toLocaleString() }
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
          已下载 {{ cachedCount }} / {{ totalChunks }} 分块
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
        {{ isFullyDownloaded ? '下载完成' : '下载全部诗词数据' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
