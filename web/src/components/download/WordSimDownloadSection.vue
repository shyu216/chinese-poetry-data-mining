<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline } from '@vicons/ionicons5'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { useWordSimilarityMetadata, WORD_SIMILARITY_STORAGE } from '@/composables/useMetadataLoader'
import { getCache, getMetadata } from '@/composables/useCacheV2'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'

const emit = defineEmits<{
  downloaded: []
}>()

const wordSimV2 = useWordSimilarityV2()
const wordSimMeta = useWordSimilarityMetadata()
const chunkLoader = useChunkLoader()

const totalChunks = ref(0)
const vocabSize = ref(0)
const vocabCached = ref(false)
const cachedChunkIds = ref<number[]>([])
const isLoadingStats = ref(false)

const cachedCount = computed(() => cachedChunkIds.value.length)
const isFullyDownloaded = computed(() => vocabCached.value && cachedCount.value === totalChunks.value && totalChunks.value > 0)
const progressPercentage = computed(() => {
  if (!vocabCached.value) return 0
  return totalChunks.value > 0 ? Math.round((cachedCount.value / totalChunks.value) * 100) : 0
})

const loadingHint = computed(() => {
  if (!vocabCached.value) return '📖 正在加载词表...'
  const loaded = cachedCount.value
  if (loaded === 0) return '🚀 准备下载...'
  if (isFullyDownloaded.value) return '✅ 词境数据已准备就绪'
  return `🔗 正在下载 ${loaded.toLocaleString()} / ${totalChunks.value} 个分块...`
})

const loadStats = async () => {
  isLoadingStats.value = true
  try {
    const index = await wordSimMeta.loadMetadata()
    totalChunks.value = index?.total_chunks || 0
    vocabSize.value = index?.vocab_size || 0

    const vocab = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')
    vocabCached.value = vocab !== null && Object.keys(vocab).length > 0

    const meta = await getMetadata(WORD_SIMILARITY_STORAGE)
    if (meta) {
      cachedChunkIds.value = meta.loadedChunkIds || []
    }
  } finally {
    isLoadingStats.value = false
  }
}

const downloadAll = async () => {
  try {
    const index = await wordSimMeta.loadMetadata()
    totalChunks.value = index?.total_chunks || 0
    vocabSize.value = index?.vocab_size || 0

    if (!vocabCached.value) {
      await wordSimV2.loadVocab()
      vocabCached.value = true
    }

    const total = totalChunks.value
    const allChunkIds = Array.from({ length: total }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !cachedChunkIds.value.includes(id))

    if (unloadedChunkIds.length === 0) {
      return
    }

    await chunkLoader.loadChunks<number[]>(unloadedChunkIds, async (chunkId: number) => {
      const vocabSize = wordSimV2.vocabSize.value
      const totalChunks = wordSimV2.totalChunks.value
      const wordsPerChunk = Math.ceil(vocabSize / totalChunks)
      const startWordId = chunkId * wordsPerChunk
      const endWordId = Math.min((chunkId + 1) * wordsPerChunk, vocabSize)
      const wordIds = Array.from({ length: endWordId - startWordId }, (_, i) => startWordId + i)
      await wordSimV2.preloadChunks(wordIds)
      return wordIds
    }, {
      chunkDelay: 50,
      onChunkLoaded: (_, data) => {
        const chunkId = Math.floor((data as number[])[0]! / Math.ceil(wordSimV2.vocabSize.value / wordSimV2.totalChunks.value))
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
  totalChunks,
  vocabCached
})
</script>

<template>
  <NCard title="🔗 词境探索数据" class="download-section">
    <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
      词境探索数据库包含 {{ vocabSize.toLocaleString() }} 个词汇的相似度数据，共 {{ totalChunks }} 个分块。
    </NAlert>

    <NProgress
      type="line"
      :percentage="progressPercentage"
      :indicator-placement="'inside'"
      :status="isFullyDownloaded ? 'success' : 'default'"
      style="margin-bottom: 16px;"
    />

    <ChunkLoaderStatus
      v-if="chunkLoader.isLoading.value || cachedCount > 0 || vocabCached"
      :is-loading="chunkLoader.isLoading.value"
      :is-paused="chunkLoader.isPaused.value"
      :progress="Math.round((cachedCount / (totalChunks || 1)) * 100)"
      :loaded-count="cachedCount"
      :total-count="totalChunks"
      title="下载词境数据"
      :hint="loadingHint"
      :stats="[
        { label: '词表状态', value: vocabCached ? '已缓存' : '未缓存' },
        { label: '已缓存分块', value: cachedCount.toLocaleString() }
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
          {{ vocabCached ? `已下载 ${cachedCount} / ${totalChunks} 分块` : '词表未缓存' }}
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
        {{ isFullyDownloaded ? '下载完成' : '下载全部词境数据' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
