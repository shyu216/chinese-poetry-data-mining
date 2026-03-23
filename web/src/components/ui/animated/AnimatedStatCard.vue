<script setup lang="ts">
import { ref, computed, type Component } from 'vue'
import { NStatistic } from 'naive-ui'
import AnimatedNumber from './AnimatedNumber.vue'

interface Props {
  label: string
  value: number
  suffix?: string
  prefixIcon?: Component
  animationDelay?: number
  animationDuration?: number
  glowColor?: string
  trend?: 'up' | 'down' | 'neutral'
}

const props = withDefaults(defineProps<Props>(), {
  suffix: '',
  animationDelay: 0,
  animationDuration: 1500,
  glowColor: 'rgba(139, 38, 53, 0.15)',
  trend: 'neutral'
})

const isVisible = ref(false)

const trendColors = {
  up: '#059669',
  down: '#DC2626',
  neutral: '#8b2635'
}

const trendIcon = computed(() => {
  switch (props.trend) {
    case 'up': return '↑'
    case 'down': return '↓'
    default: return ''
  }
})

const startAnimation = () => {
  setTimeout(() => {
    isVisible.value = true
  }, props.animationDelay)
}

defineExpose({
  startAnimation
})
</script>

<template>
  <div
    class="animated-stat-card"
    :class="{ 'is-visible': isVisible, [`trend-${trend}`]: true }"
    :style="{ '--glow-color': glowColor, animationDelay: `${animationDelay}ms` }"
  >
    <div class="stat-icon-wrap">
      <component :is="prefixIcon" v-if="prefixIcon" class="stat-icon" />
    </div>
    <div class="stat-content">
      <AnimatedNumber
        :value="value"
        :duration="animationDuration"
        class="stat-number"
      />
      <span class="stat-suffix">{{ suffix }}</span>
      <span class="stat-label">{{ label }}</span>
    </div>
    <div class="stat-glow"></div>
    <span v-if="trend !== 'neutral'" class="trend-indicator">{{ trendIcon }}</span>
  </div>
</template>

<style scoped>
.animated-stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--color-bg, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 12px;
  overflow: hidden;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.animated-stat-card.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.animated-stat-card:hover {
  border-color: var(--color-seal, #8b2635);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(139, 38, 53, 0.12);
}

.stat-icon-wrap {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 38, 53, 0.1) 0%, rgba(139, 38, 53, 0.05) 100%);
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-icon {
  width: 28px;
  height: 28px;
  color: var(--color-seal, #8b2635);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.stat-number {
  font-family: "Noto Serif SC", serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--color-ink, #2c3e50);
  line-height: 1.2;
}

.stat-suffix {
  font-size: 14px;
  color: var(--color-ink-light, #666);
  margin-left: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--color-ink-light, #666);
  letter-spacing: 1px;
}

.stat-glow {
  position: absolute;
  top: 50%;
  right: -20px;
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, var(--glow-color) 0%, transparent 70%);
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.animated-stat-card:hover .stat-glow {
  opacity: 1;
}

.trend-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 12px;
  font-weight: 600;
}

.trend-up .trend-indicator {
  color: #059669;
}

.trend-down .trend-indicator {
  color: #DC2626;
}

.trend-up .stat-number {
  color: #059669;
}

.trend-down .stat-number {
  color: #DC2626;
}

@media (max-width: 768px) {
  .animated-stat-card {
    padding: 16px;
  }

  .stat-icon-wrap {
    width: 44px;
    height: 44px;
  }

  .stat-icon {
    width: 22px;
    height: 22px;
  }

  .stat-number {
    font-size: 24px;
  }
}
</style>
