import { ref, shallowRef, computed, type ComputedRef } from 'vue'
import { loadWordSimilarityChunk, type WordSimilarityChunk } from './useWordSimilarityFbs'
import {
  getCachedWordSimilarityVocab,
  cacheWordSimilarityVocab,
  getCachedWordSimilarityChunk,
  cacheWordSimilarityChunk,
  getWordSimilarityCacheStats
} from './usePoemCache'

interface WordSimilarityMetadata {
  total_words: number
  total_chunks: number
  vocab_size: number
  similarity_threshold: number
}

// 反向词表: word -> word_id
const vocabReverse = shallowRef<Map<string, number>>(new Map())
// 正向词表: word_id -> word (从 chunk 中累积)
const vocabForward = shallowRef<Map<number, string>>(new Map())
// 词到 chunk 的映射
const wordToChunkMap = shallowRef<Map<number, number>>(new Map())
// 已加载的 chunk 数据
const loadedChunks = shallowRef<Map<number, WordSimilarityChunk>>(new Map())

const isLoading = ref(false)
const isReady = ref(false)
const error = ref<string | null>(null)
const metadata = shallowRef<WordSimilarityMetadata | null>(null)
const loadedCount = ref(0)
const totalChunks = ref(0)

// 加载元数据
async function loadMetadata(): Promise<WordSimilarityMetadata> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/word_similarity_v3/metadata.json`)
  if (!response.ok) {
    throw new Error(`Failed to load metadata: ${response.status}`)
  }
  return response.json()
}

// 加载词表
async function loadVocab(): Promise<Map<string, number>> {
  // 先尝试从缓存读取
  const cached = await getCachedWordSimilarityVocab()
  if (cached) {
    console.log('[useWordSimilarity] Using cached vocab')
    return new Map(Object.entries(cached))
  }

  const response = await fetch(`${import.meta.env.BASE_URL}data/word_similarity_v3/vocab.json`)
  if (!response.ok) {
    throw new Error(`Failed to load vocab: ${response.status}`)
  }

  const vocabData: Record<string, number> = await response.json()

  // 缓存词表
  await cacheWordSimilarityVocab(vocabData)

  return new Map(Object.entries(vocabData))
}

// 构建词到 chunk 的映射
function buildWordToChunkMap(vocab: Map<string, number>, totalChunksNum: number): Map<number, number> {
  const map = new Map<number, number>()
  const vocabSize = vocab.size

  // 每个 chunk 大约包含的词数
  const wordsPerChunk = Math.ceil(vocabSize / totalChunksNum)

  for (let wordId = 0; wordId < vocabSize; wordId++) {
    const chunkId = Math.floor(wordId / wordsPerChunk)
    map.set(wordId, Math.min(chunkId, totalChunksNum - 1))
  }

  return map
}

// 加载指定 chunk
async function loadChunk(chunkId: number): Promise<WordSimilarityChunk> {
  // 检查内存缓存
  if (loadedChunks.value.has(chunkId)) {
    return loadedChunks.value.get(chunkId)!
  }

  // 检查 IndexedDB 缓存
  const cached = await getCachedWordSimilarityChunk(chunkId)
  if (cached) {
    console.log(`[useWordSimilarity] Using cached chunk ${chunkId}`)
    loadedChunks.value.set(chunkId, cached)
    return cached
  }

  // 从网络加载
  const chunk = await loadWordSimilarityChunk(chunkId)

  // 更新词表
  for (let i = 0; i < chunk.vocab.length; i++) {
    const word = chunk.vocab[i]
    if (word) {
      vocabForward.value.set(i, word)
    }
  }

  // 缓存到 IndexedDB
  await cacheWordSimilarityChunk(chunkId, chunk)

  loadedChunks.value.set(chunkId, chunk)
  return chunk
}

export interface UseWordSimilarityReturn {
  initialize: () => Promise<void>
  hasWord: (word: string) => boolean
  getSimilarWords: (word: string, minSimilarity?: number) => Promise<Array<{ word: string; similarity: number }>>
  getCacheStats: () => Promise<{ vocabCached: boolean; chunks: number; totalSize: number }>
  preloadChunks: (wordIds: number[]) => Promise<void>
  isReady: typeof isReady
  isLoading: typeof isLoading
  error: typeof error
  vocabSize: ComputedRef<number>
  metadata: ComputedRef<WordSimilarityMetadata | null>
}

export function useWordSimilarity(): UseWordSimilarityReturn {
  const vocabSize = computed(() => vocabReverse.value.size)

  // 初始化
  const initialize = async (): Promise<void> => {
    if (isReady.value) return

    isLoading.value = true
    error.value = null

    try {
      // 加载元数据
      const meta = await loadMetadata()
      metadata.value = meta
      totalChunks.value = meta.total_chunks

      // 加载词表
      const vocab = await loadVocab()
      vocabReverse.value = vocab

      // 构建词到 chunk 的映射
      wordToChunkMap.value = buildWordToChunkMap(vocab, meta.total_chunks)

      isReady.value = true
      console.log(`[useWordSimilarity] Initialized with ${vocab.size} words, ${meta.total_chunks} chunks`)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      console.error('[useWordSimilarity] Initialization failed:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  // 检查词是否存在
  const hasWord = (word: string): boolean => {
    return vocabReverse.value.has(word)
  }

  // 获取相似词
  const getSimilarWords = async (
    word: string,
    minSimilarity: number = 0.7
  ): Promise<Array<{ word: string; similarity: number }>> => {
    if (!isReady.value) {
      await initialize()
    }

    const wordId = vocabReverse.value.get(word)
    if (wordId === undefined) {
      return []
    }

    // 找到对应的 chunk
    const chunkId = wordToChunkMap.value.get(wordId)
    if (chunkId === undefined) {
      return []
    }

    // 加载 chunk
    const chunk = await loadChunk(chunkId)

    // 查找词条目
    const entry = chunk.entries.get(wordId)
    if (!entry) {
      return []
    }

    // 过滤并转换相似词
    const results: Array<{ word: string; similarity: number }> = []
    for (const sw of entry.similarWords) {
      if (sw.similarity >= minSimilarity) {
        const similarWord = chunk.vocab[sw.wordId] || vocabForward.value.get(sw.wordId)
        if (similarWord) {
          results.push({
            word: similarWord,
            similarity: sw.similarity
          })
        }
      }
    }

    // 按相似度排序
    return results.sort((a, b) => b.similarity - a.similarity)
  }

  // 获取缓存统计
  const getCacheStats = async () => {
    return await getWordSimilarityCacheStats()
  }

  // 预加载热门词的 chunk
  const preloadChunks = async (wordIds: number[]) => {
    const chunkIds = new Set<number>()
    for (const wordId of wordIds) {
      const chunkId = wordToChunkMap.value.get(wordId)
      if (chunkId !== undefined) {
        chunkIds.add(chunkId)
      } else {
        console.warn(`[preloadChunks] No chunk mapping for wordId: ${wordId}`)
      }
    }

    console.log(`[preloadChunks] wordIds: ${wordIds.length}, unique chunkIds: ${chunkIds.size}`)

    for (const chunkId of chunkIds) {
      if (!loadedChunks.value.has(chunkId)) {
        console.log(`[preloadChunks] Loading chunk ${chunkId}`)
        await loadChunk(chunkId)
      } else {
        console.log(`[preloadChunks] Chunk ${chunkId} already in memory`)
      }
    }
  }

  return {
    initialize,
    hasWord,
    getSimilarWords,
    getCacheStats,
    preloadChunks,
    isReady,
    isLoading,
    error,
    vocabSize,
    metadata: computed(() => metadata.value)
  }
}
