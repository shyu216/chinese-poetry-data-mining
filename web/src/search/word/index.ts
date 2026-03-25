/**
 * @overview
 * file: web/src/search/word/index.ts
 * category: search
 * tech: Vue 3 + TypeScript
 * summary: 词汇搜索模块的统一入口，导出 `wordSearch` 单例与 Vue composable `useWordSearch()`。
 *
 * Responsibilities:
 *  - 封装 `WordSearch` 单例的生命周期（初始化、错误）；为组件提供轻量的 isReady/isLoading/error 包装
 *  - 将低层的搜索实现暴露为组件友好的 API
 *
 * Potential issues & recommendations:
 *  - 组件不应在渲染路径触发大规模初始化；建议在用户交互或路由守卫中预热索引
 */

export { wordSearch } from './WordSearch'
export type { WordSearch } from './WordSearch'
export type { WordSearchResult, WordSearchOptions } from './WordSearch'

// Vue composable
import { ref, readonly } from 'vue'
import { wordSearch } from './WordSearch'
import type { WordSearchResult, WordSearchOptions } from './WordSearch'
import type { WordCountItem } from '@/composables/types'

export function useWordSearch() {
  const isReady = ref(false)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  // 立即开始初始化，不依赖 onMounted
  // 这样可以支持在 setup() 外调用
  if (!isLoading.value && !isReady.value) {
    isLoading.value = true
    wordSearch.initialize()
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

  async function search(query: string, options?: WordSearchOptions): Promise<WordSearchResult> {
    return wordSearch.search(query, options)
  }

  async function searchByLength(length: number, options?: WordSearchOptions): Promise<WordSearchResult> {
    return wordSearch.searchByLength(length, options)
  }

  async function getTopWords(topN: number = 100): Promise<WordCountItem[]> {
    return wordSearch.getTopWords(topN)
  }

  async function getWordDetail(word: string): Promise<WordCountItem | null> {
    return wordSearch.getWordDetail(word)
  }

  function getStats() {
    return wordSearch.getStats()
  }

  function clearCache() {
    wordSearch.clearCache()
  }

  return {
    isReady: readonly(isReady),
    isLoading: readonly(isLoading),
    error: readonly(error),
    search,
    searchByLength,
    getTopWords,
    getWordDetail,
    getStats,
    clearCache
  }
}
