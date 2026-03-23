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
