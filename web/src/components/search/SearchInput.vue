<script setup lang="ts">
/**
 * SearchInput - 统一搜索输入组件
 * 
 * 功能：
 * - 统一的搜索输入框样式
 * - 支持搜索图标、清空按钮
 * - 支持不同尺寸（small, medium, large）
 * - 支持加载状态显示
 */
import { NInput } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'

interface Props {
  modelValue: string
  placeholder?: string
  size?: 'small' | 'medium' | 'large'
  width?: string | number
  loading?: boolean
  disabled?: boolean
  clearable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索',
  size: 'medium',
  width: 220,
  loading: false,
  disabled: false,
  clearable: true
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'search': [value: string]
  'clear': []
}>()

const handleInput = (value: string) => {
  emit('update:modelValue', value)
}

const handleKeyup = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    emit('search', props.modelValue)
  }
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
}

const widthStyle = typeof props.width === 'number' ? `${props.width}px` : props.width
</script>

<template>
  <div class="search-input-wrapper" :style="{ width: widthStyle }">
    <NInput
      :value="modelValue"
      :placeholder="placeholder"
      :size="size"
      :loading="loading"
      :disabled="disabled"
      :clearable="clearable"
      @update:value="handleInput"
      @keyup="handleKeyup"
      @clear="handleClear"
    >
      <template #prefix>
        <SearchOutline class="search-icon" />
      </template>
    </NInput>
  </div>
</template>

<style scoped>
.search-input-wrapper {
  display: inline-block;
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--n-text-color-disabled);
}
</style>
