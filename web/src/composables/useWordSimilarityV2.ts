/**
 * 文件: web/src/composables/useWordSimilarityV2.ts
 * 说明: 管理词相似度数据的加载、缓存、验证与访问接口，基于 FlatBuffers 格式存储分片数据并提供按需加载能力。
 *
 * 数据管线:
 *   - 元数据读取: 通过 `useWordSimilarityMetadata` 获取 vocab 大小与分片信息。
 *   - 缓存验证: 使用 `getValidatedMetadata` 与 `computeVocabHash` 验证本地 IndexedDB 缓存一致性。
 *   - 分片加载: 使用 `getVerifiedChunk` / FlatBuffers 解析器读取分片并转换为内存友好的结构（Map/数组）。
 *   - 索引构建: 构建 `vocabCache`, `vocabReverseCache` 与 `wordToChunkMap`，供查询与相似词计算使用。
 *
 * 复杂度:
 *   - 单词查找/映射为 O(1)（Map），构建映射或遍历词表为 O(n)，加载单个分片为 O(c)（c=分片内元素数）。
 *   - 空间: 客户端缓存词表与分片导致空间复杂度为 O(n)（n = 词汇总量，或已缓存条目数）。
 *
 * 关键技术/“黑科技”:
 *   - FlatBuffers: 二进制快速访问，减少 JSON 解析开销与内存复制。
 *   - 验证与版本控制: `getValidatedMetadata` 与 `computeVocabHash` 用于防止缓存不一致。
 *
 * 潜在问题/建议:
 *   - 虽然 FlatBuffers 减少了解析成本，但分片解析仍在主线程执行，面对大型分片应使用 Web Worker 或流式解析以避免 UI 卡顿。
 *   - 缓存元数据与分片不一致时需要健壮的回退/修复策略（当前实现有 autoClean，但需监控边缘情况）。
 */
import { ref, computed, type Ref } from 'vue'
import * as flatbuffers from 'flatbuffers'
import type { WordSimilarityData, WordSimilarityMetadata, SimilarWordResult } from './types'
import { useWordSimilarityMetadata, WORD_SIMILARITY_STORAGE } from './useMetadataLoader'
import { getCache, setCache, getMetadata, setMetadata, clearStorage, getValidatedMetadata } from './useCacheV2'
import { getVerifiedCache, getVerifiedChunk } from './useVerifiedCache'
import { WordSimilarityFile } from '@/generated/word-similarity/word-similarity-file'

interface WordSimilarityChunk {
  vocab: string[]
  entries: Map<number, {
    /** FastText 内部索引，非真实词频 */
    frequency: number
    similarWords: Array<{ wordId: number; similarity: number }>
  }>
}

/** 存储版本号，每次数据结构变更时递增 */
const STORAGE_VERSION = 1

const vocabCache = ref<Map<string, number>>(new Map())
const vocabReverseCache = ref<Map<number, string>>(new Map())
const wordToChunkMap = ref<Map<number, number>>(new Map())
const chunkCache = new Map<number, WordSimilarityChunk>()
const loadedChunkIds: Ref<number[]> = ref([])

/**
 * 计算词汇表的哈希值，用于验证缓存一致性
 */
function computeVocabHash(vocab: Record<string, number>): string {
  const entries = Object.entries(vocab)
  const sample = entries.slice(0, Math.min(100, entries.length))
  return `${entries.length}:${sample.map(([k, v]) => `${k}=${v}`).join(',')}`
}

/**
 * 初始化加载的 chunk IDs，带版本验证
 */
async function initLoadedChunkIds() {
  // 使用版本验证获取元数据
  const meta = await getValidatedMetadata(
    WORD_SIMILARITY_STORAGE,
    STORAGE_VERSION,
    {
      getDependencyHash: async () => {
        const vocab = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')
        return vocab ? computeVocabHash(vocab) : null
      },
      autoClean: true
    }
  )

  if (meta && meta.loadedChunkIds) {
    const validIds = meta.loadedChunkIds.filter((id: number) => id < (meta.totalChunks || 0))
    loadedChunkIds.value = validIds
    if (validIds.length !== meta.loadedChunkIds.length) {
      await setMetadata(WORD_SIMILARITY_STORAGE, {
        loadedChunkIds: validIds,
        totalChunks: meta.totalChunks,
        version: STORAGE_VERSION
      })
    }
  } else {
    // 验证失败或没有元数据，重置状态
    loadedChunkIds.value = []
  }
}
initLoadedChunkIds()

export function useWordSimilarityV2() {
  const { metadata: wordSimMeta, loading, error, loadMetadata } = useWordSimilarityMetadata()

  const vocabSize = computed(() => wordSimMeta.value?.vocab_size || 0)
  const totalChunks = computed(() => wordSimMeta.value?.total_chunks || 0)

  async function loadVocab(): Promise<Map<string, number>> {
    if (vocabCache.value.size > 0) {
      return vocabCache.value
    }

    const result = await getVerifiedCache<Record<string, number>>(
      WORD_SIMILARITY_STORAGE,
      'vocab',
      'word_similarity_v3/vocab.json',
      async () => {
        const response = await fetch(`${import.meta.env.BASE_URL}data/word_similarity_v3/vocab.json`)
        if (!response.ok) throw new Error('Failed to load vocab')
        return response.json()
      }
    )

    if (!result.data) {
      const errorMsg = result.error || 'Data is null'
      console.error('[useWordSimilarityV2] loadVocab failed:', {
        error: errorMsg,
        valid: result.valid,
        fromCache: result.fromCache,
        hashMatch: result.hashMatch
      })
      throw new Error(`Failed to load vocab: ${errorMsg}`)
    }

    vocabCache.value = new Map(Object.entries(result.data))
    vocabReverseCache.value = new Map(Object.entries(result.data).map(([k, v]) => [v, k]))

    return vocabCache.value
  }

  function buildWordToChunkMap(vocabSize: number, totalChunks: number): Map<number, number> {
    if (wordToChunkMap.value.size > 0) {
      return wordToChunkMap.value
    }

    const wordsPerChunk = Math.ceil(vocabSize / totalChunks)
    const map = new Map<number, number>()

    for (let wordId = 0; wordId < vocabSize; wordId++) {
      const chunkId = Math.floor(wordId / wordsPerChunk)
      map.set(wordId, Math.min(chunkId, totalChunks - 1))
    }

    wordToChunkMap.value = map
    return map
  }

  async function loadChunk(chunkId: number): Promise<WordSimilarityChunk> {
    if (chunkCache.has(chunkId)) {
      return chunkCache.get(chunkId)!
    }

    const chunkIdStr = chunkId.toString().padStart(4, '0')
    const filePath = `word_similarity_v3/word_chunk_${chunkIdStr}.bin`

    const result = await getVerifiedChunk<{ vocab: string[], entries: [number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }][] }>(
      WORD_SIMILARITY_STORAGE,
      chunkId,
      filePath,
      async () => {
        const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
        if (!response.ok) throw new Error(`Failed to load word chunk ${chunkId}`)

        const buffer = new Uint8Array(await response.arrayBuffer())
        const chunk = await parseWordSimilarityChunk(buffer)

        return {
          vocab: chunk.vocab,
          entries: Array.from(chunk.entries.entries())
        }
      }
    )

    if (!result.data) {
      throw new Error(`Failed to load word chunk ${chunkId}: ${result.error || 'Unknown error'}`)
    }

    const chunk: WordSimilarityChunk = {
      vocab: result.data.vocab,
      entries: new Map(result.data.entries)
    }
    chunkCache.set(chunkId, chunk)

    if (!loadedChunkIds.value.includes(chunkId)) {
      loadedChunkIds.value.push(chunkId)
      // 计算当前词汇表的哈希值
      const vocabData = Object.fromEntries(vocabCache.value)
      const vocabHash = computeVocabHash(vocabData)
      await setMetadata(WORD_SIMILARITY_STORAGE, {
        loadedChunkIds: [...loadedChunkIds.value],
        totalChunks: totalChunks.value,
        version: STORAGE_VERSION,
        dependencyHash: vocabHash,
        validationData: {
          vocabSize: vocabCache.value.size,
          lastChunkLoaded: chunkId,
          loadedAt: Date.now()
        }
      })
    }

    return chunk
  }

  async function parseWordSimilarityChunk(buffer: Uint8Array): Promise<WordSimilarityChunk> {
    const bb = new flatbuffers.ByteBuffer(buffer)

    const file = WordSimilarityFile.getRootAsWordSimilarityFile(bb)
    if (!file) {
      throw new Error('Invalid WRSV file: failed to parse')
    }

    const vocabLen = file.vocabLength()
    const vocab: string[] = new Array(vocabLen)
    let vocabCount = 0
    for (let i = 0; i < vocabLen; i++) {
      const word = file.vocab(i)
      if (word) {
        vocab[vocabCount++] = word
      }
    }
    vocab.length = vocabCount

    const entries = new Map<number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }>()

    const wordsLen = file.wordsLength()
    for (let i = 0; i < wordsLen; i++) {
      const entry = file.words(i)
      if (!entry) continue

      const wordId = entry.wordId()
      const frequency = entry.frequency()

      const swLen = entry.similarWordsLength()
      const similarWords: Array<{ wordId: number; similarity: number }> = new Array(swLen)
      let swCount = 0
      for (let j = 0; j < swLen; j++) {
        const sw = entry.similarWords(j)
        if (sw) {
          similarWords[swCount++] = {
            wordId: sw.wordId(),
            similarity: sw.similarity() / 10000
          }
        }
      }
      similarWords.length = swCount

      entries.set(wordId, { frequency, similarWords })
    }

    return { vocab, entries }
  }

  async function initialize(): Promise<void> {
    const meta = await loadMetadata()
    await loadVocab()
    buildWordToChunkMap(meta.vocab_size, meta.total_chunks)
  }

  async function hasWord(word: string): Promise<boolean> {
    if (vocabCache.value.size === 0) {
      await loadVocab()
    }
    return vocabCache.value.has(word)
  }

  async function getSimilarWords(
    word: string,
    options?: {
      minSimilarity?: number
      maxResults?: number
    }
  ): Promise<SimilarWordResult[]> {
    if (vocabCache.value.size === 0) {
      await loadVocab()
    }

    const wordId = vocabCache.value.get(word)
    if (wordId === undefined) {
      return []
    }

    const chunkId = wordToChunkMap.value.get(wordId)
    if (chunkId === undefined) {
      return []
    }

    const chunk = await loadChunk(chunkId)
    const entry = chunk.entries.get(wordId)

    if (!entry) {
      return []
    }

    const minSimilarity = options?.minSimilarity ?? 0
    const maxResults = options?.maxResults ?? 20

    let similarWords = entry.similarWords
      .filter(sw => sw.similarity >= minSimilarity)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, maxResults)

    return similarWords.map(sw => {
      const similarWord = chunk.vocab[sw.wordId] || vocabReverseCache.value.get(sw.wordId) || ''
      return {
        word: similarWord,
        similarity: sw.similarity,
        frequency: entry.frequency
      }
    })
  }

  async function getWordFrequency(word: string): Promise<number> {
    if (vocabCache.value.size === 0) {
      await loadVocab()
    }

    const wordId = vocabCache.value.get(word)
    if (wordId === undefined) {
      return 0
    }

    const chunkId = wordToChunkMap.value.get(wordId)
    if (chunkId === undefined) {
      return 0
    }

    const chunk = await loadChunk(chunkId)
    const entry = chunk.entries.get(wordId)

    return entry?.frequency || 0
  }

  async function getWordInfo(word: string): Promise<WordSimilarityData | null> {
    if (vocabCache.value.size === 0) {
      await loadVocab()
    }

    const wordId = vocabCache.value.get(word)
    if (wordId === undefined) {
      return null
    }

    const chunkId = wordToChunkMap.value.get(wordId)
    if (chunkId === undefined) {
      return null
    }

    const chunk = await loadChunk(chunkId)
    const entry = chunk.entries.get(wordId)

    if (!entry) {
      return null
    }

    const similarWords = entry.similarWords
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 20)
      .map(sw => ({
        word: chunk.vocab[sw.wordId] || vocabReverseCache.value.get(sw.wordId) || '',
        similarity: sw.similarity
      }))

    return {
      word,
      frequency: entry.frequency,
      similarWords
    }
  }

  async function searchSimilarWords(
    words: string[],
    options?: {
      minSimilarity?: number
      maxResults?: number
    }
  ): Promise<Array<{ word: string; totalSimilarity: number }>> {
    const wordSims: Map<string, number> = new Map()

    for (const word of words) {
      const similar = await getSimilarWords(word, options)
      for (const sw of similar) {
        const current = wordSims.get(sw.word) || 0
        wordSims.set(sw.word, current + sw.similarity)
      }
    }

    return Array.from(wordSims.entries())
      .map(([word, totalSimilarity]) => ({ word, totalSimilarity }))
      .sort((a, b) => b.totalSimilarity - a.totalSimilarity)
      .slice(0, options?.maxResults || 20)
  }

  function getLoadedChunkCount(): number {
    return loadedChunkIds.value.length
  }

  async function preloadChunks(chunkIds: number[]): Promise<void> {
    const concurrency = 5
    for (let i = 0; i < chunkIds.length; i += concurrency) {
      const batch = chunkIds.slice(i, i + concurrency)
      await Promise.all(batch.map(id => loadChunk(id)))
      if (i % 10 === 0) await new Promise(resolve => setTimeout(resolve, 0))
    }
  }

  async function clearCache(): Promise<void> {
    vocabCache.value.clear()
    vocabReverseCache.value.clear()
    wordToChunkMap.value.clear()
    chunkCache.clear()
    loadedChunkIds.value = []
    await clearStorage(WORD_SIMILARITY_STORAGE)
  }

  return {
    metadata: wordSimMeta,
    vocabSize,
    totalChunks,
    loading,
    error,
    loadMetadata,
    loadChunk,
    loadVocab,
    initialize,
    hasWord,
    getSimilarWords,
    getWordFrequency,
    getWordInfo,
    searchSimilarWords,
    getLoadedChunkCount,
    preloadChunks,
    clearCache,
    getVocabReverseMap: () => vocabReverseCache.value
  }
}
