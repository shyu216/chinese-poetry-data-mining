<!--
  @overview
  file: web/src/components/display/StatsCard.vue
  category: frontend-component
  tech: Vue 3 + TypeScript
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(UI 组件)
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 路径特征: web/src/components/display/StatsCard.vue
-->
<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
  label: string
  value: string | number
  suffix?: string
  prefixIcon?: Component
  trend?: 'up' | 'down' | 'neutral'
}

const props = withDefaults(defineProps<Props>(), {
  trend: 'neutral'
})

const trendColors = {
  up: '#059669',
  down: '#DC2626',
  neutral: '#8b2635'
}
</script>

<template>
  <div class="stat-card" :class="`trend-${trend}`">
    <div class="stat-icon-wrapper" v-if="prefixIcon">
      <component :is="prefixIcon" class="stat-icon" />
    </div>
    <div class="stat-content">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value-wrapper">
        <span class="stat-value">{{ value }}</span>
        <span v-if="suffix" class="stat-suffix">{{ suffix }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s ease;
  min-width: 0;
}

.stat-card:hover {
  border-color: var(--color-seal, #8b2635);
  box-shadow: 0 2px 6px rgba(139, 38, 53, 0.08);
}

.stat-icon-wrapper {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: rgba(139, 38, 53, 0.06);
}

.stat-icon {
  width: 18px;
  height: 18px;
  color: v-bind('trendColors[trend]');
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--color-ink-light, #888);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-value-wrapper {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.stat-value {
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  line-height: 1.3;
}

.trend-up .stat-value {
  color: #059669;
}

.trend-down .stat-value {
  color: #DC2626;
}

.stat-suffix {
  font-size: 12px;
  color: var(--color-ink-light, #999);
}

/* 移动端适配 */
@media (max-width: 640px) {
  .stat-card {
    padding: 8px 10px;
    gap: 6px;
  }

  .stat-icon-wrapper {
    width: 28px;
    height: 28px;
  }

  .stat-icon {
    width: 16px;
    height: 16px;
  }

  .stat-label {
    font-size: 11px;
  }

  .stat-value {
    font-size: 14px;
  }

  .stat-suffix {
    font-size: 11px;
  }
}

/* 超小屏幕 */
@media (max-width: 380px) {
  .stat-card {
    padding: 6px 8px;
  }

  .stat-icon-wrapper {
    width: 24px;
    height: 24px;
  }

  .stat-icon {
    width: 14px;
    height: 14px;
  }

  .stat-value {
    font-size: 13px;
  }
}
</style>
