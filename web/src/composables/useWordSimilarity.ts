/**
 * 词相似度 Composable
 * 在 Vue 组件中使用词相似度数据
 *
 * 使用示例:
 * ```vue
 * <script setup>
 * import { useWordSimilarity } from '@/composables/useWordSimilarity'
 *
 * const { isReady, getSimilarWords, hasWord } = useWordSimilarity()
 *
 * // 获取相似词
 * const similarWords = await getSimilarWords('春风', 0.8)
 * </script>
 * ```
 */

import { ref, computed } from 'vue'
import { wordSimilarityLoader } from '@/utils/wordSimilarityLoader'

// 全局状态（单例模式）
const isInitialized = ref(false)
const isLoading = ref(false)
const error = ref<string | null>(null)
const vocabSize = ref(0)

/**
 * 初始化加载器
 */
async function initializeLoader(): Promise<void> {
  if (isInitialized.value) return
  if (isLoading.value) return

  isLoading.value = true
  error.value = null

  try {
    await wordSimilarityLoader.initialize()
    vocabSize.value = wordSimilarityLoader.getVocabSize()
    isInitialized.value = true
  } catch (err) {
    error.value = err instanceof Error ? err.message : '初始化失败'
    console.error('Word similarity loader initialization failed:', err)
  } finally {
    isLoading.value = false
  }
}

/**
 * 词相似度 Composable
 */
export function useWordSimilarity() {
  // 确保初始化
  if (!isInitialized.value && !isLoading.value) {
    initializeLoader()
  }

  /**
   * 获取词的相似词列表
   */
  async function getSimilarWords(
    word: string,
    minSimilarity?: number
  ): Promise<{ word: string; similarity: number }[]> {
    if (!isInitialized.value) {
      await initializeLoader()
    }
    return wordSimilarityLoader.getSimilarWords(word, minSimilarity)
  }

  /**
   * 批量获取多个词的相似词
   */
  async function getSimilarWordsBatch(
    words: string[],
    minSimilarity?: number
  ): Promise<Map<string, { word: string; similarity: number }[]>> {
    if (!isInitialized.value) {
      await initializeLoader()
    }
    return wordSimilarityLoader.getSimilarWordsBatch(words, minSimilarity)
  }

  /**
   * 检查词是否存在
   */
  function hasWord(word: string): boolean {
    return wordSimilarityLoader.hasWord(word)
  }

  /**
   * 获取词的 ID
   */
  function getWordId(word: string): number | undefined {
    return wordSimilarityLoader.getWordId(word)
  }

  /**
   * 通过 ID 获取词
   */
  function getWordById(id: number): string | undefined {
    return wordSimilarityLoader.getWordById(id)
  }

  /**
   * 获取元数据
   */
  function getMetadata() {
    return wordSimilarityLoader.getMetadata()
  }

  /**
   * 清除缓存
   */
  function clearCache(): void {
    wordSimilarityLoader.clearCache()
  }

  return {
    // 状态
    isReady: computed(() => isInitialized.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    vocabSize: computed(() => vocabSize.value),

    // 方法
    getSimilarWords,
    getSimilarWordsBatch,
    hasWord,
    getWordId,
    getWordById,
    getMetadata,
    clearCache,

    // 重新初始化
    reinitialize: initializeLoader
  }
}

// 默认导出
export default useWordSimilarity
