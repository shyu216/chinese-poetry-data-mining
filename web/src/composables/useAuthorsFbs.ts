import * as flatbuffers from 'flatbuffers'
import { AuthorChunkFile } from '@/generated/author-chunk/author-chunk-file'
import { Author } from '@/generated/author-chunk/author'
import { WordFreq } from '@/generated/author-chunk/word-freq'
import { MeterPattern } from '@/generated/author-chunk/meter-pattern'
import { SimilarAuthor } from '@/generated/author-chunk/similar-author'
import type { AuthorStats } from '@/types/author'

/**
 * 将 FlatBuffers 的 WordFreq 转换为普通对象
 */
function convertWordFreq(wf: WordFreq): { word: string; count: number } {
  return {
    word: wf.word() || '',
    count: wf.count()
  }
}

/**
 * 将 FlatBuffers 的 MeterPattern 转换为普通对象
 */
function convertMeterPattern(mp: MeterPattern): { pattern: string; count: number } {
  return {
    pattern: mp.pattern() || '',
    count: mp.count()
  }
}

/**
 * 将 FlatBuffers 的 SimilarAuthor 转换为普通对象
 */
function convertSimilarAuthor(sa: SimilarAuthor): { author: string; similarity: number } {
  return {
    author: sa.author() || '',
    similarity: sa.similarity()
  }
}

/**
 * 将 FlatBuffers 的 Author 转换为 AuthorStats
 */
function convertAuthor(author: Author): AuthorStats {
  // 转换诗体类型计数
  const poemTypeCounts: Record<string, number> = {}
  const poemTypeCountsLen = author.poemTypeCountsLength()
  for (let i = 0; i < poemTypeCountsLen; i++) {
    const wf = author.poemTypeCounts(i)
    if (wf) {
      const word = wf.word()
      if (word) {
        poemTypeCounts[word] = wf.count()
      }
    }
  }

  // 转换格律模式
  const meterPatterns: Array<{ pattern: string; count: number }> = []
  const meterPatternsLen = author.meterPatternsLength()
  for (let i = 0; i < meterPatternsLen; i++) {
    const mp = author.meterPatterns(i)
    if (mp) {
      meterPatterns.push(convertMeterPattern(mp))
    }
  }

  // 转换词频
  const wordFrequency: Record<string, number> = {}
  const wordFreqLen = author.wordFrequencyLength()
  for (let i = 0; i < wordFreqLen; i++) {
    const wf = author.wordFrequency(i)
    if (wf) {
      const word = wf.word()
      if (word) {
        wordFrequency[word] = wf.count()
      }
    }
  }

  // 转换相似诗人
  const similarAuthors: Array<{ author: string; similarity: number }> = []
  const similarAuthorsLen = author.similarAuthorsLength()
  for (let i = 0; i < similarAuthorsLen; i++) {
    const sa = author.similarAuthors(i)
    if (sa) {
      similarAuthors.push(convertSimilarAuthor(sa))
    }
  }

  // 转换诗词ID列表
  const poemIds: string[] = []
  const poemIdsLen = author.poemIdsLength()
  for (let i = 0; i < poemIdsLen; i++) {
    const id = author.poemIds(i)
    if (id) {
      poemIds.push(id)
    }
  }

  return {
    author: author.author() || '',
    poem_count: author.poemCount(),
    poem_ids: poemIds,
    poem_type_counts: poemTypeCounts,
    meter_patterns: meterPatterns,
    word_frequency: wordFrequency,
    similar_authors: similarAuthors
  }
}

/**
 * 解析 FlatBuffers 二进制数据为 AuthorStats 数组
 */
export function parseAuthorChunkFbs(buffer: Uint8Array): AuthorStats[] {
  const bb = new flatbuffers.ByteBuffer(buffer)
  
  // 检查文件标识符
  if (!AuthorChunkFile.bufferHasIdentifier(bb)) {
    throw new Error('Invalid FBS file: wrong identifier')
  }
  
  const chunkFile = AuthorChunkFile.getRootAsAuthorChunkFile(bb)
  const authors: AuthorStats[] = []
  
  const authorsLen = chunkFile.authorsLength()
  for (let i = 0; i < authorsLen; i++) {
    const author = chunkFile.authors(i)
    if (author) {
      authors.push(convertAuthor(author))
    }
  }
  
  return authors
}

/**
 * 加载单个 FBS 文件并解析
 */
export async function loadAuthorChunkFbs(chunkId: string): Promise<AuthorStats[]> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/author_v2/author_chunk_${chunkId}.fbs`)
  
  if (!response.ok) {
    throw new Error(`Failed to load chunk ${chunkId}: ${response.status}`)
  }
  
  const buffer = new Uint8Array(await response.arrayBuffer())
  return parseAuthorChunkFbs(buffer)
}
