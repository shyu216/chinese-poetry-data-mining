<!--
  文件: web/src/views/DataOverviewView.vue
  说明: 数据总览容器，在挂载时触发 `DataOverview` 组件的 `loadStats`，并用全局 loading 展示进度。

  数据管线:
    - 容器触发 -> `DataOverview.loadStats()` 执行存储统计（可能遍历 IndexedDB 或缓存元数据，成本视实现而定）。

  复杂度:
    - 容器自身为 O(1)，实际统计成本可能为 O(n)（n = 本地缓存条目数）。

  注意:
    - 统计过程可能耗时，已使用 loading 进行用户反馈；若统计非常大，建议后台任务或分片统计。
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataOverview from '@/components/data/DataOverview.vue'
import { useLoading } from '@/composables/useLoading'

const overviewRef = ref()
const loading = useLoading()

onMounted(async () => {
  console.log('[DataOverviewView] mounted, calling loadStats')

  // 开始 loading
  loading.startBlocking('数据总览', '正在统计存储数据...')

  try {
    await overviewRef.value?.loadStats()
    loading.updatePhase('complete', '统计完成')
    loading.finish()
  } catch (e) {
    loading.error('统计失败')
  }
})
</script>

<template>
  <DataOverview ref="overviewRef" />
</template>
