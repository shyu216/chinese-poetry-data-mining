import { computed, ref, type Ref } from 'vue'
import type { WordCountItem, WordCountQueryResult } from './types'
import { useWordcountMetadata, WORDCOUNT_STORAGE } from './useMetadataLoader'
import { getValidatedMetadata, setMetadata } from './useCache'
import { queryFirst, queryRows } from './useSQLiteDatabase'

const STORAGE_VERSION = 1
const wordCountCache = new Map<number, WordCountItem[]>()
const loadedChunkIds: Ref<number[]> = ref([])

async function initLoadedWordCountChunkIds() {
  const meta = await getValidatedMetadata(WORDCOUNT_STORAGE, STORAGE_VERSION, { autoClean: true })
  loadedChunkIds.value = meta?.loadedChunkIds ?? []
}
void initLoadedWordCountChunkIds()

interface WordCountRow {
  word: string
  count: number
  rank: number
  chunk_id: number
}

function toWord(row: Pick<WordCountRow, 'word' | 'count' | 'rank'>): WordCountItem {
  return {
    word: row.word,
    count: row.count,
    rank: row.rank
  }
}

async function markLoadedChunk(chunkId: number, totalChunks: number) {
  if (loadedChunkIds.value.includes(chunkId)) return
  loadedChunkIds.value = [...loadedChunkIds.value, chunkId]
  await setMetadata(WORDCOUNT_STORAGE, {
    loadedChunkIds: [...loadedChunkIds.value],
    totalChunks,
    version: STORAGE_VERSION
  })
}

export function useWordcount() {
  const { metadata: wordCountMeta, loading, error, loadMetadata } = useWordcountMetadata()

  const totalWords = computed(() => wordCountMeta.value?.total_words || 0)
  const totalChunks = computed(() => wordCountMeta.value?.total_chunks || 0)

  async function loadChunk(chunkIndex: number): Promise<WordCountItem[]> {
    if (wordCountCache.has(chunkIndex)) {
      return wordCountCache.get(chunkIndex)!
    }

    const rows = await queryRows<WordCountRow>(
      `SELECT word, count, rank, chunk_id
       FROM word_counts
       WHERE chunk_id = ?
       ORDER BY rank ASC`,
      [chunkIndex]
    )

    const items = rows.map(toWord)
    wordCountCache.set(chunkIndex, items)
    await markLoadedChunk(chunkIndex, totalChunks.value)
    return items
  }

  async function getWordCounts(startRank: number = 1, endRank: number = 1000): Promise<WordCountQueryResult> {
    const rows = await queryRows<WordCountRow>(
      `SELECT word, count, rank, chunk_id
       FROM word_counts
       WHERE rank BETWEEN ? AND ?
       ORDER BY rank ASC`,
      [startRank, endRank]
    )

    return {
      words: rows.map(toWord),
      total: totalWords.value,
      startRank,
      endRank
    }
  }

  async function getTopWords(topN: number = 100): Promise<WordCountItem[]> {
    const rows = await queryRows<WordCountRow>(
      `SELECT word, count, rank, chunk_id
       FROM word_counts
       ORDER BY count DESC, rank ASC
       LIMIT ?`,
      [topN]
    )
    return rows.map(toWord)
  }

  async function getWordsByChunk(chunkIndex: number): Promise<WordCountItem[]> {
    return loadChunk(chunkIndex)
  }

  async function searchWord(keyword: string): Promise<WordCountItem | null> {
    const row = await queryFirst<WordCountRow>(
      `SELECT word, count, rank, chunk_id
       FROM word_counts
       WHERE word = ?`,
      [keyword]
    )
    return row ? toWord(row) : null
  }

  async function getWordStats() {
    const meta = await loadMetadata()
    return {
      totalWords: meta.total_words,
      totalChunks: meta.total_chunks,
      chunkStats: meta.chunks.map(chunk => ({
        index: chunk.index,
        startRank: chunk.start_rank,
        endRank: chunk.end_rank,
        count: chunk.count,
        totalCount: chunk.total_count,
        startWord: chunk.start_word,
        endWord: chunk.end_word
      }))
    }
  }

  async function getWordsInRange(range: number): Promise<WordCountItem[]> {
    return (await getWordCounts(1, range)).words
  }

  async function getRankRangeForChunk(chunkIndex: number): Promise<{ startRank: number; endRank: number } | null> {
    const meta = await loadMetadata()
    const chunk = meta.chunks.find(item => item.index === chunkIndex)
    return chunk ? { startRank: chunk.start_rank, endRank: chunk.end_rank } : null
  }

  async function getChunkByRank(rank: number): Promise<number> {
    const row = await queryFirst<WordCountRow>(
      `SELECT chunk_id
       FROM word_counts
       WHERE rank = ?`,
      [rank]
    )
    return row?.chunk_id ?? 0
  }

  function getLoadedChunkCount(): number {
    return loadedChunkIds.value.length
  }

  async function preloadChunks(startChunk: number, endChunk: number): Promise<void> {
    await Promise.all(Array.from({ length: endChunk - startChunk + 1 }, (_, offset) => loadChunk(startChunk + offset)))
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
