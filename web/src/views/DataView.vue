<!--
  文件: web/src/views/DataView.vue
  说明: 数据管理页的容器视图，提供数据总览、下载与存储详情三个子页的路由与选项卡同步。

  数据管线:
    - 该视图本身不直接操作数据，而是作为容器协调 `DataOverviewView`, `DataDownloadView`, `DataStorageView` 三个子视图的数据加载与交互。

  复杂度:
    - 主要为路由与 UI 控制逻辑，复杂度为常数 O(1)，具体数据操作由子视图决定。

  注意:
    - 选项卡与路由之间的双向同步需避免无限路由更新循环（当前通过 computed getter/setter 实现）。
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NTabs, NTabPane } from 'naive-ui'
import { ServerOutline } from '@vicons/ionicons5'
import { PageHeader } from '@/components/layout'
import DataOverviewView from './DataOverviewView.vue'
import DataDownloadView from './DataDownloadView.vue'
import DataStorageView from './DataStorageView.vue'

const route = useRoute()
const router = useRouter()

const activeTab = computed({
  get: () => {
    const path = route.path
    if (path.includes('/overview')) return 'overview'
    if (path.includes('/download')) return 'download'
    if (path.includes('/storage')) return 'storage'
    return 'overview'
  },
  set: (value: string) => {
    console.log('[DataView] tab changed to:', value)
    router.push(`/data/${value}`)
  }
})
</script>

<template>
  <div class="data-view">
    <PageHeader
      title="数据管理"
      subtitle="管理本地缓存数据，支持离线浏览"
      :icon="ServerOutline"
    />

    <NTabs v-model:value="activeTab" type="line" size="large" class="data-tabs">
      <NTabPane name="overview" tab="总览">
        <DataOverviewView />
      </NTabPane>

      <NTabPane name="download" tab="数据下载">
        <DataDownloadView />
      </NTabPane>

      <NTabPane name="storage" tab="存储详情">
        <DataStorageView />
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.data-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.data-tabs :deep(.n-tabs-pane-wrapper) {
  padding-top: 16px;
}
</style>
