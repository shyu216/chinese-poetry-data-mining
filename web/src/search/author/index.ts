/**
 * @overview
 * file: web/src/search/author/index.ts
 * category: algorithm
 * tech: Vue 3 + TypeScript
 * solved: 实现检索与索引策略（核心导出：useAuthorSearch）
 * data_source: 组合式状态与组件内部状态
 * data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 核心导出: useAuthorSearch；关键函数: useAuthorSearch, search, searchByDynasty, getStats
 */
/**
 * AuthorSearch Module - 作者搜索模块
 */

export { authorSearch } from './AuthorSearch'
export type { AuthorSearch } from './AuthorSearch'
export type { AuthorSearchResult, AuthorSearchOptions } from './AuthorSearch'

// Vue composable
import { ref, readonly } from 'vue'
import { authorSearch } from './AuthorSearch'
import type { AuthorSearchResult, AuthorSearchOptions } from './AuthorSearch'
import type { AuthorStats } from '@/composables/types'

export function useAuthorSearch() {
  const isReady = ref(false)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  // 立即开始初始化，不依赖 onMounted
  // 这样可以支持在 setup() 外调用
  if (!isLoading.value && !isReady.value) {
    isLoading.value = true
    authorSearch.initialize()
      .then(() => {
        isReady.value = true
      })
      .catch((e) => {
        error.value = e instanceof Error ? e : new Error(String(e))
      })
      .finally(() => {
        isLoading.value = false
      })
  }

  async function search(query: string, options?: AuthorSearchOptions): Promise<AuthorSearchResult> {
    return authorSearch.search(query, options)
  }

  async function searchByDynasty(dynasty: string, options?: AuthorSearchOptions): Promise<AuthorSearchResult> {
    return authorSearch.searchByDynasty(dynasty, options)
  }

  function getStats() {
    return authorSearch.getStats()
  }

  function clearCache() {
    authorSearch.clearCache()
  }

  return {
    isReady: readonly(isReady),
    isLoading: readonly(isLoading),
    error: readonly(error),
    search,
    searchByDynasty,
    getStats,
    clearCache
  }
}
