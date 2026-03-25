<!--
  @overview
  file: web/src/components/data/DataDownload.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 组件事件
  data_flow: props 输入 -> 组件渲染(NSpace, PoemsDownloadSection, AuthorsDownloadSection) -> emit 回传
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: handleDownloaded；主渲染组件: NSpace, PoemsDownloadSection, AuthorsDownloadSection, WordCountDownloadSection
-->
<script setup lang="ts">
import { NSpace } from 'naive-ui'
import {
  PoemsDownloadSection,
  AuthorsDownloadSection,
  WordCountDownloadSection,
  WordSimDownloadSection,
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
    <WordSimDownloadSection
      @downloaded="handleDownloaded"
    />
    <KeywordIndexDownloadSection
      @downloaded="handleDownloaded"
    />
  </NSpace>
</template>
