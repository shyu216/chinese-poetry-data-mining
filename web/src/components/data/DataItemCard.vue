<script setup lang="ts">
import { computed, ref, onMounted, nextTick } from 'vue'
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

const progressPercent = computed(() => {
  if (props.totalCount === 0) return 0
  return Math.round((props.cachedCount / props.totalCount) * 100)
})

const isComplete = computed(() => {
  return props.cachedCount > 0 && props.cachedCount === props.totalCount
})

const chartRef = ref<HTMLElement>()

onMounted(async () => {
  await nextTick()
  if (chartRef.value && props.bars.length > 20) {
    chartRef.value.scrollLeft = chartRef.value.scrollWidth
  }
})
</script>

<template>
  <NCard class="data-item-card" :class="colorClass">
    <div class="card-header">
      <div class="card-title">
        <span class="card-icon">{{ icon }}</span>
        <span class="card-name">{{ title }}</span>
      </div>
      <NTag size="small" :type="isComplete ? 'success' : 'default'">
        {{ cachedCount }} / {{ totalCount }}
      </NTag>
    </div>
    
    <div class="card-description">{{ description }}</div>
    
    <div class="card-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }" :class="colorClass"></div>
      </div>
      <span class="progress-text">{{ progressPercent }}%</span>
    </div>
    
    <div class="card-chart" ref="chartRef">
      <div v-if="bars.length > 0" class="mini-bars" :class="{ 'scrollable': bars.length > 20 }">
        <div
          v-for="bar in bars"
          :key="bar.id"
          class="mini-bar"
          :class="{ 'cached': bar.cached, [colorClass]: true }"
          :style="{ height: maxCount > 0 ? (bar.count / maxCount * 100) + '%' : '0%' }"
          :title="`${bar.count}${bar.cached ? ' (已缓存)' : ''}`"
        />
      </div>
      <NEmpty v-else description="暂无数据" size="small" />
    </div>
    
    <div class="card-legend">
      <span class="legend-dot" :class="['cached', colorClass]"></span> 已缓存
      <span class="legend-dot uncached"></span> 未缓存
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

.card-chart {
  height: 60px;
  margin-bottom: 8px;
  overflow: hidden;
}

.mini-bars {
  display: flex;
  align-items: flex-end;
  height: 100%;
  gap: 2px;
  min-width: 100%;
}

.mini-bars.scrollable {
  overflow-x: auto;
  scroll-behavior: smooth;
}

.mini-bars.scrollable::-webkit-scrollbar {
  height: 4px;
}

.mini-bars.scrollable::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 2px;
}

.mini-bars.scrollable::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 2px;
}

.mini-bar {
  flex: 1;
  min-width: 4px;
  background: #e8e8e8;
  border-radius: 2px 2px 0 0;
  transition: height 0.3s ease;
}

.mini-bar.cached.poems { background: #4caf50; }
.mini-bar.cached.authors { background: #2196f3; }
.mini-bar.cached.wordcount { background: #ff9800; }
.mini-bar.cached.wordsim { background: #9c27b0; }
.mini-bar.cached.searchindex { background: #00bcd4; }
.mini-bar.cached.keywordindex { background: #ff5722; }

.card-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: #999;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.cached { background: #4caf50; }
.legend-dot.cached.authors { background: #2196f3; }
.legend-dot.cached.wordcount { background: #ff9800; }
.legend-dot.cached.wordsim { background: #9c27b0; }
.legend-dot.cached.searchindex { background: #00bcd4; }
.legend-dot.cached.keywordindex { background: #ff5722; }
.legend-dot.uncached { background: #e8e8e8; }
</style>
