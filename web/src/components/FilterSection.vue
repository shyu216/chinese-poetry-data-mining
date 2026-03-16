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
