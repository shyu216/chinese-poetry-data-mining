<!--
  @overview
  file: web/src/components/data/DataDownload.vue
  category: frontend-component / data-management
  tech: Vue 3 + TypeScript + Naive UI
  summary: 数据下载面板，聚合各类下载分区（诗词、作者、词频、索引等），触发后台分片下载并在父组件中回报完成事件。

  Data pipeline:
  - 输入: 用户点击下载按钮触发子组件（PoemsDownloadSection 等）的下载流程
  - 处理: 每个下载子组件负责分片并发下载、写入 IndexedDB、并上报进度与完成事件
  - 输出: 在全部子项下载完成后通过 `downloaded` 事件通知父组件

  Complexity & notes:
  - 单次下载为 I/O 密集型操作，受网络与磁盘写入速度限制；前端需管理并发与重试策略
  - 组件本身为控制与编排层，不直接执行重负载任务

  Recommendations:
  - 下载流程应在 `useChunkLoader` 或子组件中实现重试、断点续传与事务性写入以降低失败风险
-->
<script setup lang="ts">
import { NSpace } from 'naive-ui'
import {
  PoemsDownloadSection,
  AuthorsDownloadSection,
  WordCountDownloadSection,
  PoemIndexDownloadSection,
  KeywordIndexDownloadSection
} from '@/components/download'

const emit = defineEmits<{
  downloaded: []
}>()

const handleDownloaded = () => {
  emit('downloaded')
}
</script>

<template>
  <NSpace vertical size="large">
    <PoemsDownloadSection
      @downloaded="handleDownloaded"
    />
    <AuthorsDownloadSection
      @downloaded="handleDownloaded"
    />
    <WordCountDownloadSection
      @downloaded="handleDownloaded"
    />
    <PoemIndexDownloadSection
      @downloaded="handleDownloaded"
    />
    <KeywordIndexDownloadSection
      @downloaded="handleDownloaded"
    />
  </NSpace>
</template>
