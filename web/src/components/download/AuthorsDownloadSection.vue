<!--
  文件: web/src/components/download/AuthorsDownloadSection.vue
  说明: 提供诗人数据分片下载与进度展示，使用 chunkLoader 将未缓存分片逐个拉取并入库（IndexedDB）。

  数据管线:
    - 读取元数据（分片总数）-> 查询本地 metadata 已缓存分片 -> 计算未缓存分片列表 -> 使用 chunkLoader 下载并回写本地缓存。

  复杂度:
    - 状态计算为 O(1)，下载与写入成本为 O(t)，t = 待下载分片数；合并/索引成本依赖后端或写入逻辑。

  注意事项:
    - 下载时应限制并发与处理失败重试；大量写入 IndexedDB 需要考虑事务与批量写入以提升性能。
    - UI 仅展示下载进度，未包含网络错误自动重试或断点续传策略。
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline, CloseOutline } from '@vicons/ionicons5'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { useAuthorsMetadata, AUTHORS_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata } from '@/composables/useCacheV2'
import type { AuthorStats } from '@/types/author'

const emit = defineEmits<{
  downloaded: []
}>()

const authorsV2 = useAuthorsV2()
const authorsMeta = useAuthorsMetadata()
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
    const index = await authorsMeta.loadMetadata()
    totalChunks.value = index?.total || 0

    const meta = await getMetadata(AUTHORS_STORAGE)
    if (meta) {
      cachedChunkIds.value = meta.loadedChunkIds || []
    }
  } finally {
    isLoadingStats.value = false
  }
}

const downloadAll = async () => {
  try {
    const index = await authorsMeta.loadMetadata()
    const total = index?.total || 0
    totalChunks.value = total

    const allChunkIds = Array.from({ length: total }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !cachedChunkIds.value.includes(id))

    if (unloadedChunkIds.length === 0) {
      return
    }

    await chunkLoader.loadChunks<AuthorStats[]>(unloadedChunkIds, authorsV2.loadAuthorChunk, {
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
  <NCard title="👥 诗人数据" class="download-section">
    <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
      诗人数据库包含 {{ totalChunks }} 个分块的诗人统计数据，支持离线浏览。
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
        取消
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
        {{ isFullyDownloaded ? '已完成' : '下载全部诗人' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
