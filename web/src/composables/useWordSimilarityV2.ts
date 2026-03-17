import { ref, computed, type Ref } from 'vue'
import * as flatbuffers from 'flatbuffers'
import type { WordSimilarityData, WordSimilarityMetadata, SimilarWordResult } from './types'
import { useWordSimilarityMetadata, WORD_SIMILARITY_STORAGE } from './useMetadataLoader'
import { getCache, setCache, getChunkedCache, setChunkedCache, getMetadata, setMetadata, clearStorage } from './useCacheV2'

interface WordSimilarityChunk {
  vocab: string[]
  entries: Map<number, {
    frequency: number
    similarWords: Array<{ wordId: number; similarity: number }>
  }>
}

const vocabCache = ref<Map<string, number>>(new Map())
const vocabReverseCache = ref<Map<number, string>>(new Map())
const wordToChunkMap = ref<Map<number, number>>(new Map())
const chunkCache = new Map<number, WordSimilarityChunk>()
const loadedChunkIds: Ref<number[]> = ref([])

async function initLoadedChunkIds() {
  const meta = await getMetadata(WORD_SIMILARITY_STORAGE)
  if (meta && meta.loadedChunkIds) {
    const validIds = meta.loadedChunkIds.filter((id: number) => id < (meta.totalChunks || 0))
    loadedChunkIds.value = validIds
    if (validIds.length !== meta.loadedChunkIds.length) {
      await setMetadata(WORD_SIMILARITY_STORAGE, {
        loadedChunkIds: validIds,
        totalChunks: meta.totalChunks
      })
    }
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

    const cached = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')
    if (cached) {
      vocabCache.value = new Map(Object.entries(cached))
      vocabReverseCache.value = new Map(Object.entries(cached).map(([k, v]) => [v, k]))
      return vocabCache.value
    }

    const response = await fetch(`${import.meta.env.BASE_URL}data/word_similarity_v3/vocab.json`)
    if (!response.ok) throw new Error('Failed to load vocab')

    const vocabData: Record<string, number> = await response.json()

    await setCache(WORD_SIMILARITY_STORAGE, 'vocab', vocabData)
    vocabCache.value = new Map(Object.entries(vocabData))
    vocabReverseCache.value = new Map(Object.entries(vocabData).map(([k, v]) => [v, k]))

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

    const cached = await getChunkedCache<{ vocab: string[], entries: [number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }][] }>(WORD_SIMILARITY_STORAGE, chunkId)
    if (cached) {
      const chunk: WordSimilarityChunk = {
        vocab: cached.vocab,
        entries: new Map(cached.entries)
      }
      chunkCache.set(chunkId, chunk)
      return chunk
    }

    const chunkIdStr = chunkId.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}data/word_similarity_v3/word_chunk_${chunkIdStr}.bin`)
    if (!response.ok) throw new Error(`Failed to load word chunk ${chunkId}`)

    const buffer = new Uint8Array(await response.arrayBuffer())
    const chunk = await parseWordSimilarityChunk(buffer)

    chunkCache.set(chunkId, chunk)
    const serializableChunk = {
      vocab: chunk.vocab,
      entries: Array.from(chunk.entries.entries())
    }
    await setChunkedCache(WORD_SIMILARITY_STORAGE, chunkId, serializableChunk)

    if (!loadedChunkIds.value.includes(chunkId)) {
      loadedChunkIds.value.push(chunkId)
      await setMetadata(WORD_SIMILARITY_STORAGE, { 
        loadedChunkIds: [...loadedChunkIds.value], 
        totalChunks: totalChunks.value 
      })
    }

    return chunk
  }

  async function parseWordSimilarityChunk(buffer: Uint8Array): Promise<WordSimilarityChunk> {
    const bb = new flatbuffers.ByteBuffer(buffer)

    const WordSimilarityFile = (await import('@/generated/word-similarity/word-similarity-file')).WordSimilarityFile
    
    let file
    try {
      if (WordSimilarityFile.bufferHasIdentifier(bb)) {
        file = WordSimilarityFile.getRootAsWordSimilarityFile(bb)
      } else {
        bb.setPosition(0)
        file = WordSimilarityFile.getRootAsWordSimilarityFile(bb)
      }
    } catch (e) {
      throw new Error(`Invalid WRSV file: ${e}`)
    }

    const vocab: string[] = []
    for (let i = 0; i < file.vocabLength(); i++) {
      const word = file.vocab(i)
      if (word) vocab[i] = word
    }

    const entries = new Map<number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }>()

    for (let i = 0; i < file.wordsLength(); i++) {
      const entry = file.words(i)
      if (!entry) continue

      const wordId = entry.wordId()
      const frequency = entry.frequency()

      const similarWords: Array<{ wordId: number; similarity: number }> = []
      for (let j = 0; j < entry.similarWordsLength(); j++) {
        const sw = entry.similarWords(j)
        if (sw) {
          similarWords.push({
            wordId: sw.wordId(),
            similarity: sw.similarity() / 10000
          })
        }
      }

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
    clearCache
  }
}
