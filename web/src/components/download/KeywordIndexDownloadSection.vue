<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline, CloseOutline } from '@vicons/ionicons5'
import { useKeywordIndex } from '@/composables/useKeywordIndex'
import { useChunkLoader } from '@/composables/useChunkLoader'

const emit = defineEmits<{
  downloaded: []
}>()

const keywordIndex = useKeywordIndex()
const chunkLoader = useChunkLoader()

const totalChunks = ref(201)
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
    // 使用 computed 属性获取统计信息
    totalChunks.value = keywordIndex.totalChunks.value
    cachedChunkIds.value = [...keywordIndex.loadedChunkIds.value]
  } finally {
    isLoadingStats.value = false
  }
}

const downloadAll = async () => {
  try {
    // 确保 manifest 已加载（自动触发 O(1) 查询准备）
    await keywordIndex.searchKeywordOptimized('') // 空查询只加载 manifest
    totalChunks.value = keywordIndex.totalChunks.value

    const unloadedChunks = []
    for (let i = 0; i < totalChunks.value; i++) {
      if (!cachedChunkIds.value.includes(i)) {
        unloadedChunks.push(i)
      }
    }

    if (unloadedChunks.length === 0) {
      return
    }

    await chunkLoader.loadChunks<number>(unloadedChunks, async (index: number) => {
      await keywordIndex.loadChunk(index)
      return index
    }, {
      chunkDelay: 30,
      onChunkLoaded: (index) => {
        const idx = index as number
        if (!cachedChunkIds.value.includes(idx)) {
          cachedChunkIds.value.push(idx)
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
  <NCard title="🔑 关键词索引数据" class="download-section">
    <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
      关键词索引包含 {{ totalChunks }} 个分块的关键词-诗词映射数据，支持按关键词搜索诗词。
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
        {{ isFullyDownloaded ? '下载完成' : '下载全部关键词索引' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
