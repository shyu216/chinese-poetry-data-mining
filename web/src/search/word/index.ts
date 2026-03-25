/**
 * @overview
 * file: web/src/search/word/index.ts
 * category: algorithm
 * tech: Vue 3 + TypeScript
 * solved: 实现检索与索引策略（核心导出：useWordSearch）
 * data_source: 组合式状态与组件内部状态
 * data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 核心导出: useWordSearch；关键函数: useWordSearch, search, searchByLength, getTopWords
 */
/**
 * WordSearch Module - 词汇搜索模块
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
