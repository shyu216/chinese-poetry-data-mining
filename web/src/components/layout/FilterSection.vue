<!--
  @overview
  file: web/src/components/layout/FilterSection.vue
  category: frontend-component / layout
  tech: Vue 3 + TypeScript
  summary: 可复用的筛选区容器，封装筛选控件的布局与基本交互（清空、应用、范围选择等）。

  Data pipeline:
  - 输入: 父组件通过 props/emit 提供筛选选项与回调
  - 处理: 局部状态管理与事件回传（apply/clear），不直接访问网络或缓存
  - 输出: 通过 `emit` 将筛选变更传回父组件以触发数据重载

  Complexity & notes:
  - UI 层为 O(1) 交互成本；实际筛选影响取决于父组件对数据集的处理方式（可能为 O(n)）

  Recommendations:
  - 若筛选会触发大规模数据计算，建议在父级对计算操作节流或在 Worker 中执行
-->
<script setup lang="ts">
const props = defineProps<{
  showClearButton?: boolean
}>()

const emit = defineEmits<{
  (e: 'clear'): void
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
