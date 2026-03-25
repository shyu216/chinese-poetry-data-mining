<!--
  @overview
  file: web/src/components/ui/badge/KeywordTag.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Vue Router + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(NTag, NBadge) -> 路由联动
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: handleClick；主渲染组件: NTag, NBadge
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NTag, NBadge } from 'naive-ui'

interface Props {
  keyword: string
  count?: number
  size?: 'small' | 'medium' | 'large'
  clickable?: boolean
  type?: 'default' | 'success' | 'info' | 'warning' | 'error'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  clickable: true,
  type: 'default'
})

const router = useRouter()

type ColorStyle = { color: string; textColor: string; borderColor: string }

const defaultColorStyle: ColorStyle = { color: 'rgba(139, 38, 53, 0.08)', textColor: '#8b2635', borderColor: 'rgba(139, 38, 53, 0.2)' }

const typeColors: Record<string, ColorStyle> = {
  default: defaultColorStyle,
  success: { color: 'rgba(4, 120, 87, 0.08)', textColor: '#047857', borderColor: 'rgba(4, 120, 87, 0.2)' },
  info: { color: 'rgba(30, 64, 175, 0.08)', textColor: '#1E40AF', borderColor: 'rgba(30, 64, 175, 0.2)' },
  warning: { color: 'rgba(180, 83, 9, 0.08)', textColor: '#B45309', borderColor: 'rgba(180, 83, 9, 0.2)' },
  error: { color: 'rgba(220, 38, 38, 0.08)', textColor: '#DC2626', borderColor: 'rgba(220, 38, 38, 0.2)' }
}

const colorStyle = computed<ColorStyle>(() => {
  return typeColors[props.type] || defaultColorStyle
})

const handleClick = () => {
  if (props.clickable) {
    router.push(`/keywords?search=${encodeURIComponent(props.keyword)}`)
  }
}
</script>

<template>
  <NTag
    class="keyword-tag"
    :class="[`size-${size}`, { clickable, clickable_hover: clickable }]"
    :size="size"
    :bordered="true"
    :style="{
      background: colorStyle.color,
      color: colorStyle.textColor,
      borderColor: colorStyle.borderColor
    }"
    @click="handleClick"
  >
    <template #default>
      <span class="keyword-text">{{ keyword }}</span>
      <NBadge
        v-if="count !== undefined && count > 0"
        :value="count"
        :max="999"
        :type="type === 'default' ? 'error' : type"
        class="keyword-count"
      />
    </template>
  </NTag>
</template>

<style scoped>
.keyword-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.keyword-tag.clickable {
  cursor: pointer;
}

.keyword-tag.clickable_hover:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(139, 38, 53, 0.15);
}

.keyword-text {
  font-weight: 500;
}

.keyword-count {
  margin-left: 4px;
}

.keyword-count :deep(.n-badge-sup) {
  font-size: 10px;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
}

.size-small {
  padding: 2px 8px;
  font-size: 12px;
}

.size-medium {
  padding: 4px 12px;
  font-size: 13px;
}

.size-large {
  padding: 6px 16px;
  font-size: 14px;
}
</style>
