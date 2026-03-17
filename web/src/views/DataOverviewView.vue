<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataOverview from '@/components/data/DataOverview.vue'

const overviewRef = ref()

onMounted(() => {
  console.log('[DataOverviewView] mounted, calling loadStats')
  overviewRef.value?.loadStats()
})
</script>

<template>
  <DataOverview ref="overviewRef" />
</template>
