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
