/**
 * 文件: web/src/composables/useWordcount.ts
 * 说明: 管理词频数据的按块加载、缓存与查询接口，支持按 rank 区间读取与分片加载策略以处理大规模词表。
 *
 * 数据管线:
 *   - 读取元数据（chunks 列表）-> 通过 `getVerifiedChunk` 加载分片 JSON -> 将分片转换为内部 `WordCountItem[]` 并缓存到内存与 IndexedDB。
 *   - 提供按 rank 范围的分片读取（`getWordCounts`）、热点 topN 获取与按 chunk 访问接口。
 *
 * 复杂度:
 *   - 单片加载为 O(c)，c = 分片大小；按范围读取会加载涉及的若干分片，成本为 O(t * c)，t = 涉及分片数。
 *   - 空间: 已加载分片缓存将占用 O(k) 内存，k = 已加载条目数。
 *
 * 风险与建议:
 *   - 大型分片 JSON 的解析在主线程会导致 UI 卡顿，建议使用 Web Worker 或将分片细化为更小的 chunk。
 *   - 当前实现基于分片大小假设（例如每片 1000 条），若数据分布变化需同步更新映射逻辑。
 */
import { ref, computed, type Ref } from 'vue'
import type { WordCountItem, WordCountMeta, WordCountQueryResult } from './types'
import { useWordcountMetadata, WORDCOUNT_STORAGE } from './useMetadataLoader'
import { getMetadata, setMetadata, getValidatedMetadata } from './useCache'
import { getVerifiedChunk } from './useVerifiedCache'

/** 存储版本号 */
const STORAGE_VERSION = 1

const wordCountCache = new Map<number, WordCountItem[]>()
const loadedChunkIds: Ref<number[]> = ref([])

async function initLoadedWordCountChunkIds() {
  const meta = await getValidatedMetadata(WORDCOUNT_STORAGE, STORAGE_VERSION, { autoClean: true })
  if (meta) {
    loadedChunkIds.value = meta.loadedChunkIds
  } else {
    loadedChunkIds.value = []
  }
}
initLoadedWordCountChunkIds()

export function useWordcount() {
  const { metadata: wordCountMeta, loading, error, loadMetadata } = useWordcountMetadata()

  const totalWords = computed(() => wordCountMeta.value?.total_words || 0)
  const totalChunks = computed(() => wordCountMeta.value?.total_chunks || 0)

  async function loadChunk(chunkIndex: number): Promise<WordCountItem[]> {
    if (wordCountCache.has(chunkIndex)) {
      return wordCountCache.get(chunkIndex)!
    }

    const chunkId = chunkIndex.toString().padStart(4, '0')
    const filePath = `wordcount_v2/chunk_${chunkId}.json`

    const result = await getVerifiedChunk<[string, number, number][]>(
      WORDCOUNT_STORAGE,
      chunkIndex,
      filePath,
      async () => {
        const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
        if (!response.ok) throw new Error(`Failed to load wordcount chunk ${chunkIndex}`)
        return response.json()
      }
    )

    if (!result.data) {
      throw new Error(`Failed to load wordcount chunk ${chunkIndex}: ${result.error || 'Unknown error'}`)
    }

    const items: WordCountItem[] = result.data.map(([word, count, rank]) => ({
      word,
      count,
      rank
    }))

    wordCountCache.set(chunkIndex, items)

    if (!loadedChunkIds.value.includes(chunkIndex)) {
      loadedChunkIds.value.push(chunkIndex)
      await setMetadata(WORDCOUNT_STORAGE, {
        loadedChunkIds: [...loadedChunkIds.value],
        totalChunks: totalChunks.value,
        version: STORAGE_VERSION
      })
    }

    return items
  }

  async function getWordCounts(
    startRank: number = 1,
    endRank: number = 1000
  ): Promise<WordCountQueryResult> {
    const meta = await loadMetadata()

    const startChunk = Math.floor((startRank - 1) / 1000)
    const endChunk = Math.floor((endRank - 1) / 1000)

    const allItems: WordCountItem[] = []

    for (let chunkIdx = startChunk; chunkIdx <= endChunk && chunkIdx < meta.chunks.length; chunkIdx++) {
      const chunkData = await loadChunk(chunkIdx)
      allItems.push(...chunkData)
    }

    const filtered = allItems.filter(item => item.rank >= startRank && item.rank <= endRank)

    return {
      words: filtered,
      total: meta.total_words,
      startRank,
      endRank
    }
  }

  async function getTopWords(topN: number = 100): Promise<WordCountItem[]> {
    return (await getWordCounts(1, topN)).words
  }

  async function getWordsByChunk(chunkIndex: number): Promise<WordCountItem[]> {
    return loadChunk(chunkIndex)
  }

  async function searchWord(keyword: string): Promise<WordCountItem | null> {
    const meta = await loadMetadata()

    for (let i = 0; i < meta.chunks.length; i++) {
      const chunkData = await loadChunk(i)
      const found = chunkData.find(item => item.word === keyword)
      if (found) {
        return found
      }
    }

    return null
  }

  async function getWordStats(): Promise<{
    totalWords: number
    totalChunks: number
    chunkStats: Array<{
      index: number
      startRank: number
      endRank: number
      count: number
      totalCount: number
      startWord: string
      endWord: string
    }>
  }> {
    const meta = await loadMetadata()

    return {
      totalWords: meta.total_words,
      totalChunks: meta.total_chunks,
      chunkStats: meta.chunks.map(c => ({
        index: c.index,
        startRank: c.start_rank,
        endRank: c.end_rank,
        count: c.count,
        totalCount: c.total_count,
        startWord: c.start_word,
        endWord: c.end_word
      }))
    }
  }

  async function getWordsInRange(range: number): Promise<WordCountItem[]> {
    const meta = await loadMetadata()
    const startRank = 1
    const endRank = range
    return (await getWordCounts(startRank, endRank)).words
  }

  async function getRankRangeForChunk(chunkIndex: number): Promise<{ startRank: number; endRank: number } | null> {
    const meta = await loadMetadata()
    const chunk = meta.chunks.find(c => c.index === chunkIndex)
    if (!chunk) return null
    return { startRank: chunk.start_rank, endRank: chunk.end_rank }
  }

  async function getChunkByRank(rank: number): Promise<number> {
    const meta = await loadMetadata()
    for (const chunk of meta.chunks) {
      if (rank >= chunk.start_rank && rank <= chunk.end_rank) {
        return chunk.index
      }
    }
    return meta.chunks.length - 1
  }

  function getLoadedChunkCount(): number {
    return loadedChunkIds.value.length
  }

  async function preloadChunks(startChunk: number, endChunk: number): Promise<void> {
    const chunksToLoad = []
    for (let i = startChunk; i <= endChunk; i++) {
      chunksToLoad.push(loadChunk(i))
    }
    await Promise.all(chunksToLoad)
  }

  async function clearCache(): Promise<void> {
    wordCountCache.clear()
    loadedChunkIds.value = []
  }

  return {
    metadata: wordCountMeta,
    totalWords,
    totalChunks,
    loading,
    error,
    loadMetadata,
    loadChunk,
    getWordCounts,
    getTopWords,
    getWordsByChunk,
    searchWord,
    getWordStats,
    getWordsInRange,
    getRankRangeForChunk,
    getChunkByRank,
    getLoadedChunkCount,
    preloadChunks,
    clearCache
  }
}
