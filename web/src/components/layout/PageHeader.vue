<!--
  @overview
  file: web/src/components/layout/PageHeader.vue
  category: frontend-component / layout
  tech: Vue 3 + TypeScript
  summary: 页面头部组件，负责显示页面标题、可选副标题与图标，作为页面布局的轻量化标题栏。

  Data pipeline (conceptual):
  - 输入: 通过 `props` 接收 `title`, `subtitle`, `icon`
  - 处理: 简单渲染，无网络或复杂计算
  - 输出: 纯展示层供父组件布局使用

  Complexity & notes:
  - 运行时成本为 O(1)。若在父组件中大量重复渲染（批量列表场景），应避免不必要的 prop 变化以减少重渲染

  Recommendations:
  - 若需要国际化或可访问性增强，建议在父组件层注入 i18n 文本并补充 ARIA 属性
-->
<script setup lang="ts">
import { h } from 'vue'
import type { Component } from 'vue'

interface Props {
  title: string
  subtitle?: string
  icon?: Component
}

defineProps<Props>()
</script>

<template>
  <header class="page-header">
    <div class="header-content">
      <h1 class="page-title">
        <span v-if="icon" class="title-icon">
          <component :is="icon" />
        </span>
        {{ title }}
      </h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
  </header>
</template>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.header-content {
  margin-bottom: 16px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.title-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-seal, #8b2635);
  color: #fff;
  border-radius: 8px;
  font-size: 20px;
}

.title-icon :deep(svg) {
  width: 22px;
  height: 22px;
}

.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink-light, #666);
}

@media (max-width: 768px) {
  .page-title {
    font-size: 22px;
  }

  .title-icon {
    width: 34px;
    height: 34px;
  }
}
</style>
