<script setup lang="ts">
import { computed } from 'vue'
import { NEmpty, NButton } from 'naive-ui'
import { FileTrayOutline, RefreshOutline, SearchOutline } from '@vicons/ionicons5'

interface Props {
  type?: 'no-data' | 'not-found' | 'error'
  title?: string
  description?: string
  showAction?: boolean
  actionText?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'no-data',
  showAction: true
})

const emit = defineEmits<{
  refresh: []
  search: []
}>()

const config = computed(() => {
  const configs = {
    'no-data': {
      title: '暂无数据',
      description: '当前没有可展示的数据，请稍后再试',
      icon: FileTrayOutline
    },
    'not-found': {
      title: '未找到结果',
      description: '没有找到匹配的内容，请尝试其他关键词',
      icon: SearchOutline
    },
    'error': {
      title: '加载失败',
      description: '数据加载出现错误，请检查网络后重试',
      icon: RefreshOutline
    }
  }
  return configs[props.type]
})

const handleAction = () => {
  if (props.type === 'error') {
    emit('refresh')
  } else {
    emit('search')
  }
}
</script>

<template>
  <div class="empty-state">
    <NEmpty>
      <template #icon>
        <NIcon :component="config.icon" :size="48" />
      </template>
      <template #default>
        <h3 class="empty-title">{{ config.title }}</h3>
        <p class="empty-description">{{ config.description }}</p>
      </template>
      <template #extra>
        <NButton
          v-if="showAction"
          type="primary"
          @click="handleAction"
        >
          {{ actionText || (type === 'error' ? '重新加载' : '重新搜索') }}
        </NButton>
      </template>
    </NEmpty>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 48px 24px;
  min-height: 300px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  margin: 0 0 8px;
}

.empty-description {
  font-size: 14px;
  color: var(--color-ink-light, #666);
  margin: 0;
}
</style>
