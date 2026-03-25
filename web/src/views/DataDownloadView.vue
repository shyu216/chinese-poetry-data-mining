<!--
  @overview
  file: web/src/views/DataDownloadView.vue
  category: frontend-page
  tech: Vue 3 + TypeScript
  solved: 承载页面级交互、筛选、展示与路由联动
  data_source: 组合式状态与组件内部状态
  data_flow: 状态输入 -> 组件渲染(DataDownload)
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 主渲染组件: DataDownload
-->
<script setup lang="ts">
import { onMounted } from 'vue'
import DataDownload from '@/components/data/DataDownload.vue'

onMounted(() => {
  console.log('[DataDownloadView] mounted')
})
</script>

<template>
  <DataDownload />
</template>
