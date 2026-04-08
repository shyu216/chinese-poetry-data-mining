<!--
  @overview
  file: web/src/components/data/DataItemCard.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI
  summary: 单个数据项卡片，用于展示某类数据的缓存进度。支持操作按钮和瓦片可视化。

  Data pipeline:
  - 输入: 通过 props 接收统计（cachedCount/totalCount）与可视化条目（bars）
  - 处理: 计算进度百分比、决定完成状态并渲染瓦片矩阵
  - 输出: 纯展示/交互组件，支持 slot 注入操作按钮

  Complexity & notes:
  - 瓦片渲染使用 CSS Grid，性能良好
  - 每个分块是一个小方砖，已缓存用彩色，未缓存用轮廓
-->
<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NTag, NEmpty } from 'naive-ui'

const props = defineProps<{
  icon: string
  title: string
  description: string
  cachedCount: number
  totalCount: number
  bars: Array<{ id: number; count: number; cached: boolean }>
  maxCount: number
  colorClass: string
}>()

defineSlots<{
  action?: () => void
}>()

const progressPercent = computed(() => {
  if (props.totalCount === 0) return 0
  return Math.round((props.cachedCount / props.totalCount) * 100)
})

const isComplete = computed(() => {
  return props.cachedCount > 0 && props.cachedCount === props.totalCount
})
</script>

<template>
  <NCard class="data-item-card" :class="colorClass">
    <div class="card-header">
      <div class="card-title">
        <span class="card-icon">{{ icon }}</span>
        <span class="card-name">{{ title }}</span>
      </div>
      <div class="card-header-right">
        <NTag size="small" :type="isComplete ? 'success' : 'default'">
          {{ cachedCount }} / {{ totalCount }}
        </NTag>
        <slot name="action"></slot>
      </div>
    </div>
    
    <div class="card-description">{{ description }}</div>
    
    <div class="card-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }" :class="colorClass"></div>
      </div>
      <span class="progress-text">{{ progressPercent }}%</span>
    </div>
    
    <div class="card-tiles">
      <template v-if="bars.length > 0">
        <div
          v-for="bar in bars"
          :key="bar.id"
          class="tile"
          :class="{ 'cached': bar.cached, [colorClass]: bar.cached }"
          :title="`分块 ${bar.id}: ${bar.count} 首${bar.cached ? ' (已缓存)' : ''}`"
        />
      </template>
      <NEmpty v-else description="暂无数据" size="small" />
    </div>
    
    <div class="card-legend">
      <span class="legend-tile cached" :class="colorClass"></span> 已缓存
      <span class="legend-tile"></span> 未缓存
    </div>
  </NCard>
</template>

<style scoped>
.data-item-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  font-size: 20px;
}

.card-name {
  font-weight: 600;
  font-size: 14px;
}

.card-description {
  font-size: 12px;
  color: #666;
  margin-bottom: 12px;
  line-height: 1.4;
}

.card-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-fill.poems { background: #4caf50; }
.progress-fill.authors { background: #2196f3; }
.progress-fill.wordcount { background: #ff9800; }
.progress-fill.wordsim { background: #9c27b0; }
.progress-fill.searchindex { background: #00bcd4; }
.progress-fill.keywordindex { background: #ff5722; }

.progress-text {
  font-size: 12px;
  color: #666;
  min-width: 36px;
}

.card-tiles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(12px, 1fr));
  gap: 3px;
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
  min-height: 80px;
  margin-bottom: 8px;
}

.tile {
  aspect-ratio: 1;
  border-radius: 2px;
  background: #e8e8e8;
  border: 1px solid #d0d0d0;
  transition: all 0.2s ease;
}

.tile:hover {
  transform: scale(1.2);
  z-index: 1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.tile.cached {
  border-color: transparent;
}

.tile.cached.poems { background: #4caf50; }
.tile.cached.authors { background: #2196f3; }
.tile.cached.wordcount { background: #ff9800; }
.tile.cached.wordsim { background: #9c27b0; }
.tile.cached.searchindex { background: #00bcd4; }
.tile.cached.keywordindex { background: #ff5722; }

.card-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 11px;
  color: #999;
}

.legend-tile {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: #e8e8e8;
  border: 1px solid #d0d0d0;
  display: inline-block;
}

.legend-tile.cached {
  border-color: transparent;
}

.legend-tile.cached.poems { background: #4caf50; }
.legend-tile.cached.authors { background: #2196f3; }
.legend-tile.cached.wordcount { background: #ff9800; }
.legend-tile.cached.wordsim { background: #9c27b0; }
.legend-tile.cached.searchindex { background: #00bcd4; }
.legend-tile.cached.keywordindex { background: #ff5722; }
</style>
