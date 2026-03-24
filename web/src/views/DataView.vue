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
      title="库藏排清"
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
