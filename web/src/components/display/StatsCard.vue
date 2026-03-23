<script setup lang="ts">
import { h } from 'vue'
import type { Component } from 'vue'
import { NStatistic } from 'naive-ui'

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
    <NStatistic :label="label" :value="value">
      <template v-if="prefixIcon" #prefix>
        <component :is="prefixIcon" :style="{ color: trendColors[trend] }" class="stat-icon" />
      </template>
      <template v-if="suffix" #suffix>
        <span class="stat-suffix">{{ suffix }}</span>
      </template>
    </NStatistic>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-seal, #8b2635);
  box-shadow: 0 2px 8px rgba(139, 38, 53, 0.08);
}

.stat-card :deep(.n-statistic__label) {
  font-size: 14px;
  color: var(--color-ink-light, #666);
  margin-bottom: 8px;
}

.stat-card :deep(.n-statistic__value) {
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.stat-icon {
  font-size: 20px;
}

.stat-suffix {
  font-size: 14px;
  color: var(--color-ink-light, #999);
  margin-left: 4px;
}

.trend-up .stat-card :deep(.n-statistic__value) {
  color: #059669;
}

.trend-down .stat-card :deep(.n-statistic__value) {
  color: #DC2626;
}
</style>
