<!--
  @overview
  file: web/src/components/layout/PageHeader.vue
  category: frontend-component
  tech: Vue 3 + TypeScript
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(UI 组件)
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 路径特征: web/src/components/layout/PageHeader.vue
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
