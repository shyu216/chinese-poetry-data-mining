<script setup lang="ts">
import { computed } from 'vue'
import { NSpin, NIcon } from 'naive-ui'
import { SyncOutline } from '@vicons/ionicons5'

interface Props {
  size?: 'small' | 'medium' | 'large'
  tip?: string
  spinning?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  tip: '加载中...',
  spinning: true
})

const spinSize = computed(() => {
  const sizes = { small: 20, medium: 32, large: 48 }
  return sizes[props.size]
})
</script>

<template>
  <div class="loading-spinner" :class="`size-${size}`">
    <NSpin :size="spinSize" :show="spinning">
      <template #description>
        <span v-if="tip" class="loading-tip">{{ tip }}</span>
      </template>
      <template #icon>
        <NIcon :component="SyncOutline" class="spinner-icon" />
      </template>
    </NSpin>
  </div>
</template>

<style scoped>
.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
}

.loading-spinner.size-small {
  padding: 12px;
}

.loading-spinner.size-large {
  padding: 48px;
}

.spinner-icon {
  animation: spin 1s linear infinite;
}

.loading-tip {
  font-size: 14px;
  color: var(--color-ink-light, #999);
  margin-top: 8px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
