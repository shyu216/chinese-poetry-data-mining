<script setup lang="ts">
interface Props {
  rank: number
  showIcon?: boolean
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  showIcon: true,
  size: 'medium'
})

const rankConfig = {
  1: { color: '#FFD700', bgColor: 'rgba(255, 215, 0, 0.15)', icon: '🏆', label: '冠军' },
  2: { color: '#C0C0C0', bgColor: 'rgba(192, 192, 192, 0.15)', icon: '🥈', label: '亚军' },
  3: { color: '#CD7F32', bgColor: 'rgba(205, 127, 50, 0.15)', icon: '🥉', label: '季军' }
}

const getRankIcon = () => {
  if (props.rank <= 3) return rankConfig[props.rank as keyof typeof rankConfig]?.icon || '🏆'
  if (props.rank <= 10) return '🥇'
  if (props.rank <= 50) return '🥈'
  return '🥉'
}

const getRankColor = () => {
  return rankConfig[props.rank as keyof typeof rankConfig]?.color || '#8b7355'
}

const getRankBgColor = () => {
  return rankConfig[props.rank as keyof typeof rankConfig]?.bgColor || 'rgba(139, 115, 85, 0.1)'
}

const sizeClasses = {
  small: 'rank-small',
  medium: 'rank-medium',
  large: 'rank-large'
}
</script>

<template>
  <div
    class="rank-badge"
    :class="sizeClasses[size]"
    :style="{
      color: getRankColor(),
      backgroundColor: getRankBgColor()
    }"
  >
    <span v-if="showIcon" class="rank-icon">{{ getRankIcon() }}</span>
    <span class="rank-number">{{ rank }}</span>
  </div>
</template>

<style scoped>
.rank-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.rank-badge:hover {
  transform: scale(1.05);
}

/* Size Variants */
.rank-small {
  padding: 2px 6px;
  font-size: 12px;
}

.rank-small .rank-icon {
  font-size: 10px;
}

.rank-medium {
  padding: 4px 10px;
  font-size: 14px;
}

.rank-medium .rank-icon {
  font-size: 14px;
}

.rank-large {
  padding: 8px 16px;
  font-size: 18px;
}

.rank-large .rank-icon {
  font-size: 20px;
}

.rank-icon {
  line-height: 1;
}

.rank-number {
  font-variant-numeric: tabular-nums;
  font-family: "Noto Serif SC", serif;
}
</style>
