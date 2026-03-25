<!--
  文件: web/src/components/download/WordSimDownloadSection.vue
  说明: 提供词向量/相似度相关数据下载逻辑，展示已缓存分片与下载进度，并支持一次性拉取全部分片。

  数据管线:
    - 元数据读取: 通过 `useWordSimilarityMetadata()` 获取分片总数与词表规模。
    - 缓存检测: 尝试读取 IndexedDB/缓存中已存在的词表与分片信息（`getCache`, `getMetadata`）。
    - 分片下载: 使用 `useChunkLoader.loadChunks` 按需下载未缓存的 chunk，并在回调中进行入库或合并。

  复杂度:
    - 计算/展示统计为 O(1)，下载与合并成本为 O(t)（t = 未下载的 chunk 数），词表合并为 O(n)（n = 词汇量）。

  风险与改进:
    - 词表体积大时一次性合并与 JSON.parse 会阻塞主线程，应使用流式解析或 Web Worker。
    - 下载过程需限制并发与支持重试、断点恢复，以应对网络波动。
    - 导出/下载大文件时应支持后端生成或分块打包，避免浏览器内存耗尽。
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline, CloseOutline } from '@vicons/ionicons5'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { useWordSimilarityMetadata, WORD_SIMILARITY_STORAGE } from '@/composables/useMetadataLoader'
import { getCache, getMetadata } from '@/composables/useCacheV2'

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
  <NCard title="🔗 词频相似度数据" class="download-section">
    <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
      词频相似度数据库包含 {{ vocabSize.toLocaleString() }} 个词汇的相似度数据，共 {{ totalChunks }} 个分块。
    </NAlert>

    <NProgress
      type="line"
      :percentage="progressPercentage"
      :indicator-placement="'inside'"
      :status="isFullyDownloaded ? 'success' : (chunkLoader.isLoading.value ? 'info' : 'default')"
      :processing="chunkLoader.isLoading.value"
      :height="8"
      :border-radius="4"
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
        v-if="chunkLoader.isLoading.value"
        type="error"
        size="large"
        @click="chunkLoader.stop"
      >
        <template #icon>
          <CloseOutline />
        </template>
        取消下载
      </NButton>
      <NButton
        v-else
        type="primary"
        size="large"
        :disabled="isFullyDownloaded"
        @click="downloadAll"
      >
        <template #icon>
          <DownloadOutline />
        </template>
        {{ isFullyDownloaded ? '已完成' : '下载全部词频相似度' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
