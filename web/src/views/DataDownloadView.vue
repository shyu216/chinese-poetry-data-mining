<!--
  文件: web/src/views/DataDownloadView.vue
  说明: 数据下载容器页，挂载并渲染 `DataDownload` 组件以提供各种数据集的离线下载入口。

  数据管线:
    - 容器委托所有数据下载与进度显示逻辑给 `DataDownload` 组件，本文件仅负责挂载与路由关联。

  复杂度:
    - 容器本身为 O(1)，实际下载、分片管理与写入成本由 `DataDownload` 内部组件处理。
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
