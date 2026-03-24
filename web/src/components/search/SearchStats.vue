<script setup lang="ts">
/**
 * SearchStats - 搜索统计信息组件
 * 
 * 功能：
 * - 显示搜索结果数量
 * - 显示查询耗时
 * - 显示数据来源（缓存/内存/网络）
 * - 统一的样式和布局
 */
import { NTag, NSpace } from 'naive-ui'
import { TimeOutline, ServerOutline, FlashOutline } from '@vicons/ionicons5'

interface Props {
  total: number
  queryTime?: number
  source?: 'memory' | 'cache' | 'indexeddb' | 'network'
  visible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  queryTime: 0,
  source: 'memory',
  visible: true
})

const getSourceIcon = () => {
  switch (props.source) {
    case 'cache':
      return FlashOutline
    case 'memory':
      return ServerOutline
    default:
      return ServerOutline
  }
}

const getSourceText = () => {
  switch (props.source) {
    case 'cache':
      return '缓存'
    case 'memory':
      return '内存'
    case 'indexeddb':
      return '本地存储'
    case 'network':
      return '网络'
    default:
      return '内存'
  }
}

const getSourceType = () => {
  switch (props.source) {
    case 'cache':
      return 'success'
    case 'memory':
      return 'info'
    case 'indexeddb':
      return 'warning'
    case 'network':
      return 'default'
    default:
      return 'info'
  }
}
</script>

<template>
  <div v-if="visible" class="search-stats">
    <NSpace align="center" size="small">
      <span class="stats-text">
        {{ total.toLocaleString() }} 条
      </span>
      
      <NTag v-if="queryTime > 0" size="small" type="default" class="stats-tag">
        <template #icon>
          <TimeOutline />
        </template>
        {{ queryTime }} 毫秒
      </NTag>
      
      <NTag size="small" :type="getSourceType()" class="stats-tag">
        <template #icon>
          <component :is="getSourceIcon()" />
        </template>
        {{ getSourceText() }}
      </NTag>
    </NSpace>
  </div>
</template>

<style scoped>
.search-stats {
  padding: 8px 0;
  font-size: 14px;
  color: var(--n-text-color-3);
}

.stats-text {
  color: var(--n-text-color-2);
}

.stats-text strong {
  color: var(--n-text-color-1);
  font-weight: 600;
}

.stats-tag {
  font-size: 12px;
}

.stats-tag :deep(.n-icon) {
  font-size: 12px;
}
</style>
