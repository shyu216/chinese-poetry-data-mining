import { ref, computed, type Ref } from 'vue'
import type { WordCountItem, WordCountMeta, WordCountQueryResult } from './types'
import { useWordcountMetadata, WORDCOUNT_STORAGE } from './useMetadataLoader'
import { getChunkedCache, setChunkedCache, getMetadata, setMetadata } from './useCacheV2'

const wordCountCache = new Map<number, WordCountItem[]>()
const loadedChunkIds: Ref<number[]> = ref([])

async function initLoadedWordCountChunkIds() {
  const meta = await getMetadata(WORDCOUNT_STORAGE)
  if (meta) {
    loadedChunkIds.value = meta.loadedChunkIds
  }
}
initLoadedWordCountChunkIds()

export function useWordcountV2() {
  const { metadata: wordCountMeta, loading, error, loadMetadata } = useWordcountMetadata()

  const totalWords = computed(() => wordCountMeta.value?.total_words || 0)
  const totalChunks = computed(() => wordCountMeta.value?.total_chunks || 0)

  async function loadChunk(chunkIndex: number): Promise<WordCountItem[]> {
    if (wordCountCache.has(chunkIndex)) {
      return wordCountCache.get(chunkIndex)!
    }

    const cached = await getChunkedCache<WordCountItem[]>(WORDCOUNT_STORAGE, chunkIndex)
    if (cached) {
      wordCountCache.set(chunkIndex, cached)
      return cached
    }

    const chunkId = chunkIndex.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}data/wordcount_v2/chunk_${chunkId}.json`)
    if (!response.ok) throw new Error(`Failed to load wordcount chunk ${chunkIndex}`)

    const rawData: [string, number, number][] = await response.json()

    const items: WordCountItem[] = rawData.map(([word, count, rank]) => ({
      word,
      count,
      rank
    }))

    wordCountCache.set(chunkIndex, items)
    await setChunkedCache(WORDCOUNT_STORAGE, chunkIndex, items)

    if (!loadedChunkIds.value.includes(chunkIndex)) {
      loadedChunkIds.value.push(chunkIndex)
      await setMetadata(WORDCOUNT_STORAGE, { 
        loadedChunkIds: [...loadedChunkIds.value], 
        totalChunks: totalChunks.value 
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
