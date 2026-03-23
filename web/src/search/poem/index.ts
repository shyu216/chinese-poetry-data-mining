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

  // 立即开始初始化，不依赖 onMounted
  // 这样可以支持在 setup() 外调用
  if (!isLoading.value && !isReady.value) {
    isLoading.value = true
    poemSearch.initialize()
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

  async function search(query: string, options?: PoemSearchOptions): Promise<PoemSearchResult> {
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
