<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NGrid, NGi } from 'naive-ui'
import { BarChartOutline, PieChartOutline } from '@vicons/ionicons5'

interface Props {
  totalPoems: number
  totalAuthors: number
  totalDynasties: number
  poemsByDynasty?: Array<{ name: string; value: number }>
}

const props = withDefaults(defineProps<Props>(), {
  poemsByDynasty: () => []
})
</script>

<template>
  <div class="stats-overview">
    <NCard class="stat-item">
      <div class="stat-icon-wrapper poems">
        <BarChartOutline />
      </div>
      <div class="stat-content">
        <span class="stat-value">{{ totalPoems.toLocaleString() }}</span>
        <span class="stat-label">诗词总数</span>
      </div>
    </NCard>
    <NCard class="stat-item">
      <div class="stat-icon-wrapper authors">
        <PieChartOutline />
      </div>
      <div class="stat-content">
        <span class="stat-value">{{ totalAuthors.toLocaleString() }}</span>
        <span class="stat-label">诗人词人</span>
      </div>
    </NCard>
    <NCard class="stat-item">
      <div class="stat-icon-wrapper dynasties">
        <BarChartOutline />
      </div>
      <div class="stat-content">
        <span class="stat-value">{{ totalDynasties }}</span>
        <span class="stat-label">朝代</span>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.stats-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--color-bg-paper, #fff);
}

.stat-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  font-size: 24px;
}

.stat-icon-wrapper.poems {
  background: rgba(139, 38, 53, 0.1);
  color: #8b2635;
}

.stat-icon-wrapper.authors {
  background: rgba(30, 64, 175, 0.1);
  color: #1E40AF;
}

.stat-icon-wrapper.dynasties {
  background: rgba(4, 120, 87, 0.1);
  color: #047857;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-ink, #2c3e50);
  font-family: "Noto Serif SC", serif;
}

.stat-label {
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

@media (max-width: 768px) {
  .stats-overview {
    grid-template-columns: 1fr;
  }
}
</style>
