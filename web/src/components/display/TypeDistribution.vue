<!--
  @overview
  file: web/src/components/display/TypeDistribution.vue
  category: frontend-component
  tech: Vue 3 + TypeScript
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(UI 组件)
  complexity: 常见查询/筛选 O(n)，排序 O(n log n)，空间复杂度常见 O(n)
  unique: 路径特征: web/src/components/display/TypeDistribution.vue
-->
<script setup lang="ts">
interface TypeItem {
  type: string
  count: number
  percentage?: number
}

interface Props {
  data: TypeItem[]
  maxItems?: number
  showPercentage?: boolean
  showBar?: boolean
  barColor?: string
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  maxItems: 5,
  showPercentage: true,
  showBar: true,
  barColor: 'var(--color-seal, #8b2635)',
  size: 'medium'
})

const displayData = computed(() => {
  const sorted = [...props.data].sort((a, b) => b.count - a.count)
  const limited = sorted.slice(0, props.maxItems)

  const total = limited.reduce((sum, item) => sum + item.count, 0)

  return limited.map(item => ({
    ...item,
    percentage: item.percentage ?? Math.round((item.count / total) * 100)
  }))
})

const maxCount = computed(() => {
  return Math.max(...displayData.value.map(item => item.count))
})

const sizeClasses = {
  small: 'size-small',
  medium: 'size-medium',
  large: 'size-large'
}
</script>

<script lang="ts">
import { computed } from 'vue'
export default {
  name: 'TypeDistribution'
}
</script>

<template>
  <div class="type-distribution" :class="sizeClasses[size]">
    <div
      v-for="(item, index) in displayData"
      :key="item.type"
      class="type-item"
      :style="{ animationDelay: `${index * 50}ms` }"
    >
      <div class="type-info">
        <span class="type-name">{{ item.type }}</span>
        <span class="type-count">
          {{ item.count.toLocaleString() }}
          <span v-if="showPercentage" class="type-percentage">
            ({{ item.percentage }}%)
          </span>
        </span>
      </div>
      <div v-if="showBar" class="type-bar-container">
        <div
          class="type-bar"
          :style="{
            width: `${(item.count / maxCount) * 100}%`,
            backgroundColor: barColor
          }"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.type-distribution {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  opacity: 0;
  animation: slideIn 0.4s ease forwards;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.type-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-name {
  font-weight: 500;
  color: var(--color-ink, #2c3e50);
}

.type-count {
  color: var(--color-ink-light, #666);
  font-variant-numeric: tabular-nums;
}

.type-percentage {
  color: var(--color-ink-light, #999);
  font-size: 0.9em;
}

.type-bar-container {
  height: 4px;
  background: var(--color-border, #e8e8e8);
  border-radius: 2px;
  overflow: hidden;
}

.type-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

/* Size Variants */
.size-small .type-name,
.size-small .type-count {
  font-size: 12px;
}

.size-small .type-bar-container {
  height: 3px;
}

.size-medium .type-name,
.size-medium .type-count {
  font-size: 14px;
}

.size-large .type-name {
  font-size: 16px;
}

.size-large .type-count {
  font-size: 14px;
}

.size-large .type-bar-container {
  height: 6px;
}
</style>
