<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataStorage from '@/components/data/DataStorage.vue'

const storageRef = ref()

onMounted(() => {
  console.log('[DataStorageView] mounted, calling loadStorageDetails')
  storageRef.value?.loadStorageDetails()
})
</script>

<template>
  <DataStorage ref="storageRef" />
</template>
