/**
 * @overview
 * file: web/src/search/poem/index.ts
 * category: algorithm
 * tech: Vue 3 + TypeScript
 * solved: 实现检索与索引策略（核心导出：usePoemSearch）
 * data_source: 组合式状态与组件内部状态
 * data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 核心导出: usePoemSearch；关键函数: usePoemSearch, ensureInitialized, search, getStats
 */
/**
 * PoemSearch Module - 诗词搜索模块
 */

export { poemSearch } from './PoemSearch'
export type { PoemSearch } from './PoemSearch'
export type { PoemSearchResult, PoemSearchOptions } from './PoemSearch'

// Vue composable
import { ref, readonly } from 'vue'
import { poemSearch } from './PoemSearch'
import type { PoemSearchResult, PoemSearchOptions } from './PoemSearch'
import type { PoemSummary } from '@/composables/types'

export function usePoemSearch() {
  const isReady = ref(false)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  // 延迟初始化：只在第一次搜索时才初始化
  let initializationTriggered = false

  async function ensureInitialized() {
    if (isReady.value || isLoading.value) return
    
    if (!initializationTriggered) {
      initializationTriggered = true
      isLoading.value = true
      try {
        await poemSearch.initialize()
        isReady.value = true
      } catch (e) {
        error.value = e instanceof Error ? e : new Error(String(e))
      } finally {
        isLoading.value = false
      }
    }
  }

  async function search(query: string, options?: PoemSearchOptions): Promise<PoemSearchResult> {
    await ensureInitialized()
    return poemSearch.search(query, options)
  }

  function getStats() {
    return poemSearch.getStats()
  }

  function clearCache() {
    poemSearch.clearCache()
  }

  return {
    isReady: readonly(isReady),
    isLoading: readonly(isLoading),
    error: readonly(error),
    search,
    getStats,
    clearCache
  }
}
