<script setup lang="ts">
import { h } from 'vue'
import type { Component } from 'vue'
import { NCard, NCollapse, NCollapseItem } from 'naive-ui'
import { ChevronDownOutline, ChevronForwardOutline } from '@vicons/ionicons5'

interface Props {
  title: string
  subtitle?: string
  icon?: Component
  collapsible?: boolean
  defaultExpanded?: boolean
  borderless?: boolean
}

withDefaults(defineProps<Props>(), {
  collapsible: false,
  defaultExpanded: true,
  borderless: false
})

const emit = defineEmits<{
  expand: [expanded: boolean]
}>()
</script>

<template>
  <section class="content-section">
    <NCard 
      :bordered="!borderless"
      :content-style="{ padding: borderless ? '0' : undefined }"
    >
      <template #header>
        <div class="section-header">
          <div class="header-left">
            <span v-if="icon" class="section-icon">
              <component :is="icon" />
            </span>
            <div class="header-text">
              <h2 class="section-title">{{ title }}</h2>
              <p v-if="subtitle" class="section-subtitle">{{ subtitle }}</p>
            </div>
          </div>
          <div class="header-right">
            <slot name="actions" />
          </div>
        </div>
      </template>

      <NCollapse 
        v-if="collapsible" 
        :default-expanded-names="defaultExpanded ? [title] : []"
        @update:expanded-names="(names: string[]) => emit('expand', names.includes(title))"
      >
        <NCollapseItem :name="title" :title="title">
          <template #header-extra>
            <slot name="collapse-extra" />
          </template>
          <div class="section-content">
            <slot />
          </div>
        </NCollapseItem>
      </NCollapse>

      <div v-else class="section-content">
        <slot />
      </div>

      <template v-if="$slots.footer" #footer>
        <slot name="footer" />
      </template>
    </NCard>
  </section>
</template>

<style scoped>
.content-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.section-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-seal, #8b2635);
  color: #fff;
  border-radius: 8px;
  font-size: 18px;
  flex-shrink: 0;
}

.section-icon :deep(svg) {
  width: 20px;
  height: 20px;
}

.header-text {
  flex: 1;
  min-width: 0;
}

.section-title {
  margin: 0;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.section-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-content {
  color: var(--color-ink, #2c3e50);
}

:deep(.n-collapse) {
  background: transparent;
}

:deep(.n-collapse-item) {
  margin-top: 0;
}

:deep(.n-collapse-item__header) {
  padding: 0;
}

:deep(.n-collapse-item__header-main) {
  display: none;
}

:deep(.n-collapse-item__content-inner) {
  padding-top: 16px;
}
</style>
