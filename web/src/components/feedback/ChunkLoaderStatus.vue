<!--
  @overview
  file: web/src/components/feedback/ChunkLoaderStatus.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props；组件事件
  data_flow: props 输入 -> 组件渲染(NCard, NBadge, NProgress) -> emit 回传
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 主渲染组件: NCard, NBadge, NProgress, NSpace
-->
<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NProgress, NButton, NSpace, NBadge } from 'naive-ui'
import { PlayOutline, PauseOutline } from '@vicons/ionicons5'

interface Props {
  isLoading: boolean
  isPaused: boolean
  progress: number
  loadedCount: number
  totalCount: number
  title?: string
  description?: string
  hint?: string
  stats?: Array<{ label: string; value: string | number }>
}

const props = withDefaults(defineProps<Props>(), {
  title: '加载中',
  description: '正在加载',
  hint: ''
})

const emit = defineEmits<{
  pause: []
  resume: []
}>()

const percentage = computed(() => Math.min(100, Math.max(0, props.progress)))

const statusText = computed(() => {
  if (!props.isLoading) return '已完成'
  if (props.isPaused) return '已暂停'
  return '加载中...'
})

const statusType = computed(() => {
  if (!props.isLoading) return 'success'
  if (props.isPaused) return 'warning'
  return 'info'
})
</script>

<template>
  <NCard v-if="props.isLoading" class="chunk-loader-status" :class="{ 'is-loading': isLoading, 'is-paused': isPaused }">
    <div class="loader-header">
      <div class="loader-title">
        <span class="title-text">{{ title }}</span>
        <NBadge :value="statusText" :type="statusType" />
      </div>
      <span class="loader-count">
        {{ loadedCount.toLocaleString() }} / {{ totalCount.toLocaleString() }}
      </span>
    </div>

    <div class="progress-wrapper">
      <NProgress
        type="line"
        :percentage="percentage"
        :indicator-placement="'inside'"
        :status="isPaused ? 'warning' : 'success'"
        :height="12"
        :border-radius="6"
        :processing="isLoading && !isPaused"
      />
    </div>

    <div v-if="hint" class="loader-hint">
      {{ hint }}
    </div>

    <div v-if="stats && stats.length > 0" class="loader-stats">
      <div v-for="stat in stats" :key="stat.label" class="stat-item">
        <span class="stat-label">{{ stat.label }}</span>
        <span class="stat-value">{{ stat.value }}</span>
      </div>
    </div>

    <div v-if="isLoading" class="loader-actions">
      <NSpace>
        <NButton
          v-if="isPaused"
          type="primary"
          size="small"
          @click="emit('resume')"
        >
          <template #icon>
            <PlayOutline />
          </template>
          继续
        </NButton>
        <NButton
          v-else
          size="small"
          @click="emit('pause')"
        >
          <template #icon>
            <PauseOutline />
          </template>
          暂停
        </NButton>
      </NSpace>
    </div>
  </NCard>
</template>

<style scoped>
.chunk-loader-status {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
}

.chunk-loader-status.is-loading {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-color: #86efac;
}

.chunk-loader-status.is-paused {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #fcd34d;
}

.loader-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.loader-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.loader-count {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.progress-wrapper {
  margin-bottom: 12px;
}

.loader-hint {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 6px;
}

.loader-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-top: 12px;
  border-top: 1px dashed #cbd5e1;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.loader-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

@media (max-width: 768px) {
  .loader-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .loader-stats {
    flex-wrap: wrap;
    gap: 16px;
  }

  .loader-actions {
    justify-content: flex-start;
  }
}
</style>
