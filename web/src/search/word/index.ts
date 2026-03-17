/**
 * WordSearch Module - 词汇搜索模块
 */

export { wordSearch } from './WordSearch'
export type { WordSearch } from './WordSearch'
export type { WordSearchResult, WordSearchOptions } from './WordSearch'

// Vue composable
import { ref, onMounted, readonly } from 'vue'
import { wordSearch } from './WordSearch'
import type { WordSearchResult, WordSearchOptions } from './WordSearch'
import type { WordCountItem } from '@/composables/types'

export function useWordSearch() {
  const isReady = ref(false)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  onMounted(async () => {
    try {
      isLoading.value = true
      await wordSearch.initialize()
      isReady.value = true
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e))
    } finally {
      isLoading.value = false
    }
  })

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
