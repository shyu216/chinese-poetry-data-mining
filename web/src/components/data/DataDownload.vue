<script setup lang="ts">
import { ref } from 'vue'
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

const poemsDownloadRef = ref()
const authorsDownloadRef = ref()
const wordcountDownloadRef = ref()
const poemIndexDownloadRef = ref()
const wordSimDownloadRef = ref()
const keywordIndexDownloadRef = ref()

const handleDownloaded = () => {
  emit('downloaded')
}
</script>

<template>
  <NSpace vertical size="large">
    <PoemsDownloadSection
      ref="poemsDownloadRef"
      @downloaded="handleDownloaded"
    />
    <AuthorsDownloadSection
      ref="authorsDownloadRef"
      @downloaded="handleDownloaded"
    />
    <WordCountDownloadSection
      ref="wordcountDownloadRef"
      @downloaded="handleDownloaded"
    />
    <PoemIndexDownloadSection
      ref="poemIndexDownloadRef"
      @downloaded="handleDownloaded"
    />
    <WordSimDownloadSection
      ref="wordSimDownloadRef"
      @downloaded="handleDownloaded"
    />
    <KeywordIndexDownloadSection
      ref="keywordIndexDownloadRef"
      @downloaded="handleDownloaded"
    />
  </NSpace>
</template>
