<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NStatistic, NProgress, NTag, NSpin, NEmpty } from 'naive-ui'
import { 
  BookOutline, 
  CreateOutline, 
  BookmarkOutline,
  CloudOutline,
  DocumentsOutline,
  PeopleOutline,
  CheckmarkCircleOutline
} from '@vicons/ionicons5'

interface DataPacketProps {
  name: string
  description?: string
  poems?: number
  authors?: number
  keywords?: number
  chunks?: number
  size?: string
  lastUpdated?: string
  loading?: boolean
}

const props = withDefaults(defineProps<DataPacketProps>(), {
  loading: false
})

const stats = computed(() => {
  const items = []
  if (props.poems !== undefined) {
    items.push({ 
      label: '诗词', 
      value: props.poems, 
      icon: BookOutline,
      color: '#8b2635'
    })
  }
  if (props.authors !== undefined) {
    items.push({ 
      label: '诗人', 
      value: props.authors, 
      icon: PeopleOutline,
      color: '#1E40AF'
    })
  }
  if (props.keywords !== undefined) {
    items.push({ 
      label: '关键词', 
      value: props.keywords, 
      icon: BookmarkOutline,
      color: '#047857'
    })
  }
  return items
})
</script>

<template>
  <NCard class="data-packet" :bordered="true">
    <template #header>
      <div class="packet-header">
        <div class="packet-icon">
          <CloudOutline />
        </div>
        <div class="packet-title-wrap">
          <h3 class="packet-title">{{ name }}</h3>
          <p v-if="description" class="packet-description">{{ description }}</p>
        </div>
      </div>
    </template>

    <NSpin :show="loading" size="medium">
      <div v-if="!loading && stats.length === 0" class="empty-state">
        <NEmpty description="暂无数据" />
      </div>

      <div v-else class="packet-stats">
        <div 
          v-for="stat in stats" 
          :key="stat.label" 
          class="stat-row"
        >
          <div class="stat-icon-wrap" :style="{ background: `${stat.color}15`, color: stat.color }">
            <component :is="stat.icon" />
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stat.value.toLocaleString() }}</span>
            <span class="stat-label">{{ stat.label }}</span>
          </div>
        </div>
      </div>
    </NSpin>

    <template v-if="chunks || size || lastUpdated" #footer>
      <div class="packet-footer">
        <div v-if="chunks" class="footer-item">
          <DocumentsOutline />
          <span>{{ chunks }} 个数据包</span>
        </div>
        <div v-if="size" class="footer-item">
          <CreateOutline />
          <span>约 {{ size }}</span>
        </div>
        <div v-if="lastUpdated" class="footer-item">
          <CheckmarkCircleOutline />
          <span>{{ lastUpdated }}</span>
        </div>
      </div>
    </template>
  </NCard>
</template>

<style scoped>
.data-packet {
  height: 100%;
  transition: all 0.2s ease;
}

.data-packet:hover {
  border-color: var(--color-seal, #8b2635);
  box-shadow: 0 4px 12px rgba(139, 38, 53, 0.1);
}

.packet-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.packet-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-seal, #8b2635), #a63d4d);
  color: #fff;
  border-radius: 10px;
  font-size: 20px;
  flex-shrink: 0;
}

.packet-title-wrap {
  flex: 1;
  min-width: 0;
}

.packet-title {
  margin: 0;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.packet-description {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.packet-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--color-bg-paper, #fafafa);
  border-radius: 8px;
}

.stat-icon-wrap {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 18px;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--color-ink-light, #999);
}

.packet-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-ink-light, #999);
}

.footer-item svg {
  font-size: 14px;
}

.empty-state {
  padding: 20px 0;
}
</style>
