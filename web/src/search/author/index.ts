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
