<!--
  @overview
  file: web/src/views/DataOverviewView.vue
  category: frontend-page
  tech: Vue 3 + TypeScript
  solved: 承载页面级交互、筛选、展示与路由联动
  data_source: 组合式状态与组件内部状态
  data_flow: 状态输入 -> 组件渲染(DataOverview)
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 主渲染组件: DataOverview
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
