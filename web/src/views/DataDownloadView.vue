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
