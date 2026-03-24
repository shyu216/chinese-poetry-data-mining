<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline, CloseOutline } from '@vicons/ionicons5'
import { useWordcountV2 } from '@/composables/useWordcountV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { useWordcountMetadata, WORDCOUNT_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata } from '@/composables/useCacheV2'
import type { WordCountItem } from '@/composables/types'

const emit = defineEmits<{
  downloaded: []
}>()

const wordcountV2 = useWordcountV2()
const wordcountMeta = useWordcountMetadata()
const chunkLoader = useChunkLoader()

const totalChunks = ref(0)
const cachedChunkIds = ref<number[]>([])
const isLoadingStats = ref(false)

const cachedCount = computed(() => cachedChunkIds.value.length)
const isFullyDownloaded = computed(() => cachedCount.value === totalChunks.value && totalChunks.value > 0)
const progressPercentage = computed(() => 
  totalChunks.value > 0 ? Math.round((cachedCount.value / totalChunks.value) * 100) : 0
)

const loadStats = async () => {
  isLoadingStats.value = true
  try {
    const index = await wordcountMeta.loadMetadata()
    totalChunks.value = index?.total_chunks || 0

    const meta = await getMetadata(WORDCOUNT_STORAGE)
    if (meta) {
      cachedChunkIds.value = meta.loadedChunkIds || []
    }
  } finally {
    isLoadingStats.value = false
  }
}

const downloadAll = async () => {
  try {
    const index = await wordcountMeta.loadMetadata()
    const total = index?.total_chunks || 0
    totalChunks.value = total

    const allChunkIds = Array.from({ length: total }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !cachedChunkIds.value.includes(id))

    if (unloadedChunkIds.length === 0) {
      return
    }

    await chunkLoader.loadChunks<WordCountItem[]>(unloadedChunkIds, wordcountV2.loadChunk, {
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
  <NCard title="📊 词频统计数据" class="download-section">
    <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
      词频数据库包含 {{ totalChunks }} 个分块的词频统计数据，支持离线浏览。
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
          已下载 {{ cachedCount }} / {{ totalChunks }} 分块
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
        {{ isFullyDownloaded ? '已完成' : '下载全部词频' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
