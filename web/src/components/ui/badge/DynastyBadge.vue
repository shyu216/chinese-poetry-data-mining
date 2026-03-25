<!--
  @overview
  file: web/src/components/ui/badge/DynastyBadge.vue
  category: frontend-component
  tech: Vue 3 + TypeScript
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(UI 组件)
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 路径特征: web/src/components/ui/badge/DynastyBadge.vue
-->
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  dynasty: string
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium'
})

const dynastyConfig: Record<string, { color: string; bg: string; icon: string }> = {
  '唐': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', icon: '盛' },
  '宋': { color: '#1E40AF', bg: 'rgba(30, 64, 175, 0.08)', icon: '雅' },
  '元': { color: '#047857', bg: 'rgba(4, 120, 87, 0.08)', icon: '曲' },
  '明': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', icon: '文' },
  '清': { color: '#7C3AED', bg: 'rgba(124, 58, 237, 0.08)', icon: '韵' },
  '近现代': { color: '#DC2626', bg: 'rgba(220, 38, 38, 0.08)', icon: '新' }
}

const config = computed(() => {
  return dynastyConfig[props.dynasty] || { color: '#5C5244', bg: 'rgba(92, 82, 68, 0.08)', icon: '古' }
})

const sizeClasses = {
  small: 'badge-small',
  medium: 'badge-medium',
  large: 'badge-large'
}
</script>

<template>
  <span 
    class="dynasty-badge" 
    :class="sizeClasses[size]"
    :style="{ 
      color: config.color,
      background: config.bg 
    }"
  >
    {{ dynasty }}
  </span>
</template>

<style scoped>
.dynasty-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border-radius: 4px;
}

.badge-small {
  padding: 2px 6px;
  font-size: 11px;
}

.badge-medium {
  padding: 4px 10px;
  font-size: 13px;
}

.badge-large {
  padding: 6px 14px;
  font-size: 15px;
}
</style>
