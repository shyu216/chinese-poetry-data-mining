<!--
  文件: web/src/components/download/KeywordIndexDownloadSection.vue
  说明: 关键词索引下载区块，管理关键词-诗词映射索引的分片下载与本地缓存状态（默认 totalChunks = 201）。

  数据管线:
    - 触发: 通过 `keywordIndex.searchKeywordOptimized('')` 可触发 manifest 加载以获取 `totalChunks`。
    - 下载: 计算未缓存分片列表并使用 `chunkLoader.loadChunks` 逐个下载并写入本地缓存。

  复杂度:
    - 下载成本随分片数量为 O(t)，索引加载后查询接近 O(1)（基于前缀/倒排索引设计）。

  注意:
    - 加载大量关键词索引可能占用显著内存，建议按需加载或只保留热数据在内存中。
    - 需保证 manifest 与分片编号的一致性，避免重复或错位加载。
-->
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
        {{ isFullyDownloaded ? '已完成' : '下载全部关键词' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
