<!--
  文件: web/src/views/DataStorageView.vue
  说明: 数据存储详情视图，作为 `DataStorage` 组件的容器并在挂载时触发其 `loadStorageDetails` 方法以展示本地缓存信息。

  数据管线:
    - 该文件本身不执行复杂数据逻辑，负责挂载并触发 `DataStorage` 组件读取本地存储详情（例如 IndexedDB 大小、已缓存分片等）。

  复杂度:
    - 容器级别为常数 O(1)，实际存储详情读取成本由 `DataStorage` 内部实现决定（可能涉及遍历数据库的 O(n) 操作）。
-->
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
