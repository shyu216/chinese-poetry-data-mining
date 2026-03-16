import * as flatbuffers from 'flatbuffers'
import { WordSimilarityFile } from '@/generated/word-similarity/word-similarity-file'
import { WordEntry } from '@/generated/word-similarity/word-entry'
import { SimilarWord } from '@/generated/word-similarity/similar-word'

export interface WordSimilarityData {
  word: string
  frequency: number
  similarWords: Array<{
    word: string
    similarity: number
  }>
}

export interface WordSimilarityChunk {
  vocab: string[] // word_id -> word
  entries: Map<number, { // word_id -> entry data
    frequency: number
    similarWords: Array<{
      wordId: number
      similarity: number
    }>
  }>
}

/**
 * 解析 FlatBuffers 二进制数据为 WordSimilarityChunk
 */
export function parseWordSimilarityChunk(buffer: Uint8Array): WordSimilarityChunk {
  const bb = new flatbuffers.ByteBuffer(buffer)

  // 检查文件标识符
  if (!WordSimilarityFile.bufferHasIdentifier(bb)) {
    throw new Error('Invalid WRSV file: wrong identifier')
  }

  const file = WordSimilarityFile.getRootAsWordSimilarityFile(bb)

  // 读取词表
  const vocab: string[] = []
  const vocabLen = file.vocabLength()
  for (let i = 0; i < vocabLen; i++) {
    const word = file.vocab(i)
    if (word) {
      vocab[i] = word
    }
  }

  // 读取词条目
  const entries = new Map<number, {
    frequency: number
    similarWords: Array<{ wordId: number; similarity: number }>
  }>()

  const wordsLen = file.wordsLength()
  for (let i = 0; i < wordsLen; i++) {
    const entry = file.words(i)
    if (!entry) continue

    const wordId = entry.wordId()
    const frequency = entry.frequency()

    const similarWords: Array<{ wordId: number; similarity: number }> = []
    const similarLen = entry.similarWordsLength()
    for (let j = 0; j < similarLen; j++) {
      const sw = entry.similarWords(j)
      if (sw) {
        similarWords.push({
          wordId: sw.wordId(),
          similarity: sw.similarity() / 10000 // 转换回 0-1 范围
        })
      }
    }

    entries.set(wordId, { frequency, similarWords })
  }

  return { vocab, entries }
}

/**
 * 加载单个 chunk 文件
 */
export async function loadWordSimilarityChunk(chunkId: number): Promise<WordSimilarityChunk> {
  const chunkIdStr = chunkId.toString().padStart(4, '0')
  const response = await fetch(`${import.meta.env.BASE_URL}data/word_similarity_v3/word_chunk_${chunkIdStr}.bin`)

  if (!response.ok) {
    throw new Error(`Failed to load chunk ${chunkId}: ${response.status}`)
  }

  const buffer = new Uint8Array(await response.arrayBuffer())
  return parseWordSimilarityChunk(buffer)
}
