<!--
  @overview
  file: web/src/components/download/PoemIndexDownloadSection.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 本地缓存（IndexedDB）；组件事件
  data_flow: props 输入 -> 组件渲染(NCard, NAlert, NProgress) -> emit 回传
  complexity: 缓存命中常见 O(1)，筛选/聚合常见 O(n)，空间复杂度常见 O(n)
  unique: 关键函数: loadStats, downloadAll；主渲染组件: NCard, NAlert, NProgress, NSpace
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NButton, NProgress, NAlert, NSpace, NTag } from 'naive-ui'
import { DownloadOutline, CheckmarkOutline, CloseOutline } from '@vicons/ionicons5'
import { useSearchIndexV2 } from '@/composables/useSearchIndexV2'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { usePoemIndexManifest, POEM_INDEX_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata } from '@/composables/useCacheV2'
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
          已下载 {{ cachedCount }} / {{ totalPrefixes }} 项
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
        {{ isFullyDownloaded ? '已完成' : '下载全部索引' }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.download-section {
  margin-bottom: 16px;
}
</style>
