<!--
  @overview
  file: web/src/components/search/SearchContainer.vue
  category: algorithm
  tech: Vue 3 + TypeScript + Naive UI
  solved: 实现检索与索引策略（核心导出：search api）
  data_source: 本地缓存（IndexedDB）；父组件 props；组件事件
  data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: handleInput, handleSearch, handleClear；主渲染组件: NSpace, SearchInput, NButton, CloseOutline
-->
<script setup lang="ts">
/**
 * SearchContainer - 统一搜索容器组件
 * 
 * 功能：
 * - 整合搜索输入框和搜索统计
 * - 支持筛选器插槽
 * - 统一的布局和样式
 * - 支持操作按钮插槽
 */
import { NSpace, NButton } from 'naive-ui'
import { CloseOutline } from '@vicons/ionicons5'
import SearchInput from './SearchInput.vue'
import SearchStats from './SearchStats.vue'

interface Props {
  // 搜索输入
  modelValue: string
  placeholder?: string
  size?: 'small' | 'medium' | 'large'
  width?: string | number
  loading?: boolean
  
  // 搜索统计
  total: number
  queryTime?: number
  source?: 'memory' | 'cache' | 'indexeddb' | 'network'
  showStats?: boolean
  
  // 布局
  showClearButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索...',
  size: 'medium',
  width: 220,
  loading: false,
  queryTime: 0,
  source: 'memory',
  showStats: true,
  showClearButton: true
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'search': [value: string]
  'clear': []
}>()

const handleInput = (value: string) => {
  emit('update:modelValue', value)
}

const handleSearch = (value: string) => {
  emit('search', value)
}

const handleClear = () => {
  emit('clear')
}
</script>

<template>
  <div class="search-container">
    <NSpace vertical size="small">
      <!-- 搜索行 -->
      <NSpace align="center" wrap>
        <!-- 搜索输入 -->
        <SearchInput
          :model-value="modelValue"
          :placeholder="placeholder"
          :size="size"
          :width="width"
          :loading="loading"
          @update:model-value="handleInput"
          @search="handleSearch"
          @clear="handleClear"
        />
        
        <!-- 筛选器插槽 -->
        <slot name="filters" />
        
        <!-- 操作按钮插槽 -->
        <slot name="actions" />
        
        <!-- 清空按钮 -->
        <NButton
          v-if="showClearButton && modelValue"
          size="small"
          quaternary
          @click="handleClear"
        >
          <template #icon>
            <CloseOutline />
          </template>
          清空
        </NButton>
      </NSpace>
      
      <!-- 搜索统计 -->
      <SearchStats
        v-if="showStats"
        :total="total"
        :query-time="queryTime"
        :source="source"
        :visible="modelValue.length > 0 || total > 0"
      />
    </NSpace>
  </div>
</template>

<style scoped>
.search-container {
  padding: 16px;
  background-color: var(--n-card-color);
  border-radius: 8px;
  border: 1px solid var(--n-border-color);
}
</style>
