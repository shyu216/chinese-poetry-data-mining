<!--
  @overview
  file: web/src/components/layout/FilterSection.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props；组件事件
  data_flow: 状态输入 -> 组件渲染(UI 组件)
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 路径特征: web/src/components/layout/FilterSection.vue
-->
<script setup lang="ts">
import { NSpace, NButton } from 'naive-ui'
import type { Slot, VNode } from 'vue'

interface Props {
  showClearButton?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  clear: []
}>()
</script>

<template>
  <section class="filter-section">
    <div class="filter-content">
      <slot />
    </div>
    <div v-if="showClearButton" class="filter-actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<style scoped>
.filter-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 8px;
}

.filter-content {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  flex: 1;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 768px) {
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-content {
    width: 100%;
  }

  .filter-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
