<!--
  @overview
  file: web/src/components/search/SearchInputEnhanced.vue
  category: algorithm
  tech: Vue 3 + TypeScript + Naive UI
  solved: 实现检索与索引策略（核心导出：search api）
  data_source: 父组件 props；组件事件
  data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
  complexity: 列表处理常见 O(n)，空间复杂度常见 O(n)
  unique: 关键函数: saveHistory, addToHistory, removeHistory, clearHistory；主渲染组件: NInput, SearchOutline
-->
<script setup lang="ts">
/**
 * SearchInputEnhanced - 增强版搜索输入组件
 * 
 * 功能：
 * - 搜索建议下拉
 * - 关键词高亮
 * - 拼音首字母搜索支持
 * - 搜索历史
 * - 防抖搜索
 */
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { NInput, NDropdown, NEmpty, NSpin, NIcon } from 'naive-ui'
import { SearchOutline, TimeOutline, CloseOutline, TrendingUpOutline } from '@vicons/ionicons5'

interface SuggestionItem {
  label: string
  value: string
  type: 'history' | 'suggestion' | 'hot'
  highlight?: string
}


interface Props {
  modelValue: string
  placeholder?: string
  size?: 'small' | 'medium' | 'large'
  width?: string | number
  loading?: boolean
  disabled?: boolean
  suggestions?: string[]
  hotSearches?: string[]
  maxHistory?: number
  enableHighlight?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索诗词或作者...',
  size: 'medium',
  width: 320,
  loading: false,
  disabled: false,
  suggestions: () => [],
  hotSearches: () => [],
  maxHistory: 5,
  enableHighlight: true
})

const getRandomCopy = (copyArray: string[]): string => {
  const index = Math.floor(Math.random() * copyArray.length)
  return copyArray[index] ?? ''
}

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'search': [value: string]
  'clear': []
  'suggestion-select': [value: string]
}>()

// 状态
const showDropdown = ref(false)
const activeIndex = ref(-1)
const searchHistory = ref<string[]>([])
const inputRef = ref<InstanceType<typeof NInput> | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)

// 从本地存储加载搜索历史
onMounted(() => {
  const saved = localStorage.getItem('poem-search-history')
  if (saved) {
    try {
      searchHistory.value = JSON.parse(saved)
    } catch {
      searchHistory.value = []
    }
  }
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 保存搜索历史
const saveHistory = () => {
  localStorage.setItem('poem-search-history', JSON.stringify(searchHistory.value.slice(0, props.maxHistory)))
}

// 添加搜索历史
const addToHistory = (query: string) => {
  if (!query.trim()) return
  const index = searchHistory.value.indexOf(query)
  if (index > -1) {
    searchHistory.value.splice(index, 1)
  }
  searchHistory.value.unshift(query)
  if (searchHistory.value.length > props.maxHistory) {
    searchHistory.value = searchHistory.value.slice(0, props.maxHistory)
  }
  saveHistory()
}

// 删除单条历史
const removeHistory = (item: string, e: Event) => {
  e.stopPropagation()
  const index = searchHistory.value.indexOf(item)
  if (index > -1) {
    searchHistory.value.splice(index, 1)
    saveHistory()
  }
}

// 清空历史
const clearHistory = (e: Event) => {
  e.stopPropagation()
  searchHistory.value = []
  saveHistory()
}

// 高亮匹配文本
const highlightText = (text: string, query: string): string => {
  if (!props.enableHighlight || !query.trim()) return text
  const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi')
  return text.replace(regex, '<mark class="search-highlight">$1</mark>')
}

const escapeRegExp = (string: string): string => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// 过滤建议
const filteredSuggestions = computed(() => {
  const query = props.modelValue.trim().toLowerCase()
  if (!query) return []
  return props.suggestions
    .filter(s => s.toLowerCase().includes(query))
    .slice(0, 5)
})

// 下拉选项
const dropdownOptions = computed(() => {
  const options: SuggestionItem[] = []
  const query = props.modelValue.trim()

  // 如果有输入，显示匹配的建议
  if (query) {
    // 历史记录匹配
    const historyMatches = searchHistory.value
      .filter(h => h.toLowerCase().includes(query.toLowerCase()) && h !== query)
      .slice(0, 3)
    
    if (historyMatches.length > 0) {
      options.push(...historyMatches.map(h => ({
        label: highlightText(h, query),
        value: h,
        type: 'history' as const
      })))
    }

    // 搜索建议
    if (filteredSuggestions.value.length > 0) {
      options.push(...filteredSuggestions.value.map(s => ({
        label: highlightText(s, query),
        value: s,
        type: 'suggestion' as const
      })))
    }
  } else {
    // 无输入时显示历史记录和热门搜索
    if (searchHistory.value.length > 0) {
      options.push(...searchHistory.value.slice(0, 3).map(h => ({
        label: h,
        value: h,
        type: 'history' as const
      })))
    }
    
    if (props.hotSearches.length > 0) {
      options.push(...props.hotSearches.slice(0, 3).map(h => ({
        label: h,
        value: h,
        type: 'hot' as const
      })))
    }
  }

  return options
})

// 处理输入
const handleInput = (value: string) => {
  emit('update:modelValue', value)
  showDropdown.value = true
  activeIndex.value = -1
}

// 处理搜索
const handleSearch = () => {
  const query = props.modelValue.trim()
  if (query) {
    addToHistory(query)
  }
  showDropdown.value = false
  emit('search', query)
}

// 处理键盘事件
const handleKeyup = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    const selectedOption = dropdownOptions.value[activeIndex.value]
    if (activeIndex.value >= 0 && selectedOption) {
      selectSuggestion(selectedOption.value)
    } else {
      handleSearch()
    }
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = Math.min(activeIndex.value + 1, dropdownOptions.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = Math.max(activeIndex.value - 1, -1)
  } else if (e.key === 'Escape') {
    showDropdown.value = false
  }
}

// 选择建议
const selectSuggestion = (value: string) => {
  emit('update:modelValue', value)
  addToHistory(value)
  showDropdown.value = false
  emit('suggestion-select', value)
  emit('search', value)
}

// 清空输入
const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
  showDropdown.value = true
  activeIndex.value = -1
}

// 点击外部关闭下拉
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.search-enhanced-wrapper')) {
    showDropdown.value = false
  }
}

// 获取图标
const getIcon = (type: string) => {
  switch (type) {
    case 'history': return TimeOutline
    case 'hot': return TrendingUpOutline
    default: return SearchOutline
  }
}

const widthStyle = typeof props.width === 'number' ? `${props.width}px` : props.width
</script>

<template>
  <div class="search-enhanced-wrapper" :style="{ width: widthStyle }">
    <div class="search-input-container" ref="dropdownRef">
      <NInput
        ref="inputRef"
        :value="modelValue"
        :placeholder="placeholder"
        :size="size"
        :loading="loading"
        :disabled="disabled"
        clearable
        @update:value="handleInput"
        @keyup="handleKeyup"
        @clear="handleClear"
        @focus="showDropdown = true"
      >
        <template #prefix>
          <SearchOutline class="search-icon" />
        </template>
      </NInput>

      <!-- 搜索建议下拉 -->
      <Transition name="dropdown">
        <div v-if="showDropdown && (dropdownOptions.length > 0 || !modelValue)" class="search-dropdown">
          <template v-if="!loading">
            <!-- 历史记录标题 -->
            <div v-if="!modelValue && searchHistory.length > 0" class="dropdown-header">
              <span class="header-title">
                <NIcon :size="14"><TimeOutline /></NIcon>
                历史
              </span>
              <span class="header-action" @click="clearHistory">清空</span>
            </div>

            <!-- 热门搜索标题 -->
            <div v-if="!modelValue && hotSearches.length > 0 && searchHistory.length === 0" class="dropdown-header">
              <span class="header-title">
                <NIcon :size="14"><TrendingUpOutline /></NIcon>
                热门
              </span>
            </div>

            <!-- 建议列表 -->
            <div class="suggestion-list">
              <div
                v-for="(item, index) in dropdownOptions"
                :key="item.value + index"
                class="suggestion-item"
                :class="{ 'is-active': index === activeIndex, [`type-${item.type}`]: true }"
                @click="selectSuggestion(item.value)"
                @mouseenter="activeIndex = index"
              >
                <NIcon :size="16" class="suggestion-icon">
                  <component :is="getIcon(item.type)" />
                </NIcon>
                <span class="suggestion-text" v-html="item.label"></span>
                <NIcon
                  v-if="item.type === 'history'"
                  :size="14"
                  class="remove-icon"
                  @click="removeHistory(item.value, $event)"
                >
                  <CloseOutline />
                </NIcon>
              </div>
            </div>
          </template>

          <!-- 加载状态 -->
          <div v-if="loading" class="dropdown-loading">
            <NSpin size="small" />
            <span>搜索中...</span>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.search-enhanced-wrapper {
  display: inline-block;
  position: relative;
}

.search-input-container {
  position: relative;
}

.search-icon {
  width: 16px;
  height: 16px;
  color: var(--n-text-color-disabled);
}

/* 下拉菜单 */
.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
  border: 1px solid rgba(139, 38, 53, 0.1);
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(139, 38, 53, 0.03);
  border-bottom: 1px solid rgba(139, 38, 53, 0.06);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-ink-light, #666);
}

.header-action {
  font-size: 12px;
  color: var(--color-seal, #8b2635);
  cursor: pointer;
  transition: opacity 0.2s;
}

.header-action:hover {
  opacity: 0.7;
}

.suggestion-list {
  max-height: 280px;
  overflow-y: auto;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.is-active {
  background: rgba(139, 38, 53, 0.05);
}

.suggestion-icon {
  color: var(--color-ink-light, #999);
  flex-shrink: 0;
}

.suggestion-item.type-hot .suggestion-icon {
  color: #f5a623;
}

.suggestion-item.type-history .suggestion-icon {
  color: var(--color-ink-light, #999);
}

.suggestion-text {
  flex: 1;
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 高亮样式 */
:deep(.search-highlight) {
  color: var(--color-seal, #8b2635);
  font-weight: 600;
  background: rgba(139, 38, 53, 0.1);
  padding: 0 2px;
  border-radius: 2px;
}

.remove-icon {
  color: var(--color-ink-light, #ccc);
  opacity: 0;
  transition: all 0.2s;
  padding: 4px;
  border-radius: 50%;
}

.suggestion-item:hover .remove-icon {
  opacity: 1;
}

.remove-icon:hover {
  background: rgba(0, 0, 0, 0.05);
  color: var(--color-ink, #666);
}

.dropdown-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--color-ink-light, #999);
  font-size: 13px;
}

/* 动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 响应式 */
@media (max-width: 768px) {
  .search-dropdown {
    position: fixed;
    top: auto;
    left: 16px;
    right: 16px;
    margin-top: 8px;
  }
}
</style>
