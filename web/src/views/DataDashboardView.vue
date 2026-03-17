<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NTabs, NTabPane } from 'naive-ui'
import { ServerOutline } from '@vicons/ionicons5'

import DataOverview from '@/components/data/DataOverview.vue'
import DataDownload from '@/components/data/DataDownload.vue'
import DataStorage from '@/components/data/DataStorage.vue'

const activeTab = ref('overview')
const isLoadingStats = ref(false)

const overviewRef = ref()
const storageRef = ref()

const loadStats = async () => {
  isLoadingStats.value = true
  try {
    if (overviewRef.value) {
      await overviewRef.value.loadStats()
    }
    if (storageRef.value) {
      await storageRef.value.loadStorageDetails()
    }
  } finally {
    isLoadingStats.value = false
  }
}

const handleSwitchTab = (tab: string) => {
  activeTab.value = tab
}

const handleRefresh = () => {
  loadStats()
}

const handleDownloaded = () => {
  loadStats()
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="data-dashboard-v2">
    <header class="page-header">
      <h1 class="page-title">
        <ServerOutline class="title-icon" />
        数据管理中心
      </h1>
      <p class="page-subtitle">
        管理本地缓存数据，支持离线浏览
      </p>
    </header>

    <NTabs v-model:value="activeTab" type="line" size="large" class="dashboard-tabs">
      <NTabPane name="overview" tab="总览">
        <DataOverview
          ref="overviewRef"
          :is-loading-stats="isLoadingStats"
          @switch-tab="handleSwitchTab"
          @refresh="handleRefresh"
        />
      </NTabPane>

      <NTabPane name="download" tab="数据下载">
        <DataDownload @downloaded="handleDownloaded" />
      </NTabPane>

      <NTabPane name="storage" tab="存储详情">
        <DataStorage
          ref="storageRef"
          :is-loading-stats="isLoadingStats"
        />
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.data-dashboard-v2 {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  width: 32px;
  height: 32px;
  color: #8b2635;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
}

.dashboard-tabs {
  margin-top: 24px;
}
</style>
