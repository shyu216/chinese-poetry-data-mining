<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NTag, NIcon } from 'naive-ui'
import { TrendingUpOutline, ColorPaletteOutline } from '@vicons/ionicons5'

interface Props {
  meter: string
  pattern: string
  tonePattern?: string
}

const props = defineProps<Props>()

const toneColors = {
  '平': '#059669',
  '仄': '#DC2626',
  '中': '#7C3AED'
}
</script>

<template>
  <NCard class="meter-pattern-card" size="small">
    <template #header>
      <div class="meter-header">
        <NIcon :component="TrendingUpOutline" />
        <span class="meter-title">格律</span>
        <NTag type="info" size="small">{{ meter }}</NTag>
      </div>
    </template>
    <div class="meter-content">
      <div class="pattern-row">
        <span class="pattern-label">句式：</span>
        <span class="pattern-value">{{ pattern }}</span>
      </div>
      <div v-if="tonePattern" class="pattern-row">
        <span class="pattern-label">平仄：</span>
        <span class="tone-pattern">
          <span
            v-for="(char, index) in tonePattern"
            :key="index"
            class="tone-char"
            :style="{ color: toneColors[char as keyof typeof toneColors] || '#666' }"
          >
            {{ char }}
          </span>
        </span>
      </div>
    </div>
  </NCard>
</template>

<style scoped>
.meter-pattern-card {
  background: var(--color-bg-paper, #fff);
}

.meter-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meter-title {
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.meter-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pattern-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pattern-label {
  font-size: 13px;
  color: var(--color-ink-light, #666);
  min-width: 40px;
}

.pattern-value {
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
}

.tone-pattern {
  font-family: monospace;
  font-size: 14px;
  letter-spacing: 2px;
}

.tone-char {
  display: inline-block;
  width: 20px;
  text-align: center;
}
</style>
