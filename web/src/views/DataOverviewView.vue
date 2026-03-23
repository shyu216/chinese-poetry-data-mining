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
