<!--
  @overview
  file: web/src/components/search/SearchStats.vue
  category: algorithm
  tech: Vue 3 + TypeScript + Naive UI
  solved: 实现检索与索引策略（核心导出：search api）
  data_source: 本地缓存（IndexedDB）；父组件 props
  data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: getSourceIcon, getSourceText, getSourceType；主渲染组件: NSpace, NTag, TimeOutline
-->
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
