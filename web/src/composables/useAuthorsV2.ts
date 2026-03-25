/**
 * @overview
 * file: web/src/composables/useAuthorsV2.ts
 * category: pipeline
 * tech: Vue 3 + TypeScript + FlatBuffers
 * solved: 封装数据加载与状态编排（关键函数：initLoadedAuthorChunkIds, convertWordFreq, convertMeterPattern）
 * data_source: public/data 静态分块文件；本地缓存（IndexedDB）
 * data_flow: 参数输入 -> 读取缓存/远端 -> 数据校验与归一化 -> 输出响应式状态
 * complexity: 常见查询/筛选 O(n)，排序 O(n log n)，空间复杂度常见 O(n)
 * unique: 核心导出: useAuthorsV2；关键函数: initLoadedAuthorChunkIds, convertWordFreq, convertMeterPattern, convertSimilarAuthor
 */
import { ref, shallowRef, computed, type Ref } from 'vue'
import * as flatbuffers from 'flatbuffers'
import type { AuthorStats, AuthorFilter, AuthorQueryResult, AuthorsIndex } from './types'
import { useAuthorsMetadata, AUTHORS_STORAGE } from './useMetadataLoader'
import { getMetadata, setMetadata, getValidatedMetadata } from './useCacheV2'
import { getVerifiedChunk } from './useVerifiedCache'
import { AuthorChunkFile } from '@/generated/author-chunk/author-chunk-file'
import { Author } from '@/generated/author-chunk/author'
import { WordFreq } from '@/generated/author-chunk/word-freq'
import { MeterPattern } from '@/generated/author-chunk/meter-pattern'
import { SimilarAuthor } from '@/generated/author-chunk/similar-author'

/** 存储版本号 */
const STORAGE_VERSION = 1

const authorsCache = shallowRef<Map<number, AuthorStats[]>>(new Map())
const loadedAuthorChunkIds: Ref<number[]> = ref([])

async function initLoadedAuthorChunkIds() {
  const meta = await getValidatedMetadata(AUTHORS_STORAGE, STORAGE_VERSION, { autoClean: true })
  if (meta) {
    loadedAuthorChunkIds.value = meta.loadedChunkIds
  } else {
    loadedAuthorChunkIds.value = []
  }
}
initLoadedAuthorChunkIds()

function convertWordFreq(wf: WordFreq): { word: string; count: number } {
  return {
    word: wf.word() || '',
    count: wf.count()
  }
}

function convertMeterPattern(mp: MeterPattern): { pattern: string; count: number } {
  return {
    pattern: mp.pattern() || '',
    count: mp.count()
  }
}

function convertSimilarAuthor(sa: SimilarAuthor): { author: string; similarity: number } {
  return {
    author: sa.author() || '',
    similarity: sa.similarity()
  }
}

function convertAuthor(author: Author): AuthorStats {
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

  const meterPatternsLen = author.meterPatternsLength()
  const meterPatterns: Array<{ pattern: string; count: number }> = new Array(meterPatternsLen)
  let meterCount = 0
  for (let i = 0; i < meterPatternsLen; i++) {
    const mp = author.meterPatterns(i)
    if (mp) {
      const pattern = mp.pattern()
      if (pattern) {
        meterPatterns[meterCount++] = { pattern, count: mp.count() }
      }
    }
  }
  meterPatterns.length = meterCount

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

  const similarAuthorsLen = author.similarAuthorsLength()
  const similarAuthors: Array<{ author: string; similarity: number }> = new Array(similarAuthorsLen)
  let similarCount = 0
  for (let i = 0; i < similarAuthorsLen; i++) {
    const sa = author.similarAuthors(i)
    if (sa) {
      const authorName = sa.author()
      if (authorName) {
        similarAuthors[similarCount++] = { author: authorName, similarity: sa.similarity() }
      }
    }
  }
  similarAuthors.length = similarCount

  const poemIdsLen = author.poemIdsLength()
  const poemIds: string[] = new Array(poemIdsLen)
  let poemIdCount = 0
  for (let i = 0; i < poemIdsLen; i++) {
    const id = author.poemIds(i)
    if (id) {
      poemIds[poemIdCount++] = id
    }
  }
  poemIds.length = poemIdCount

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

export function useAuthorsV2() {
  const { metadata: authorsIndex, loading, error, loadMetadata } = useAuthorsMetadata()

  const totalAuthors = computed(() => authorsIndex.value?.totalAuthors || 0)
  const totalChunks = computed(() => authorsIndex.value?.total || 0)
  const loadedChunkCount = computed(() => loadedAuthorChunkIds.value.length)

  async function loadAuthorChunk(chunkId: number): Promise<AuthorStats[]> {
    if (authorsCache.value.has(chunkId)) {
      return authorsCache.value.get(chunkId)!
    }

    const chunkIdStr = chunkId.toString().padStart(4, '0')
    const filePath = `author_v2/author_chunk_${chunkIdStr}.fbs`

    const result = await getVerifiedChunk<AuthorStats[]>(
      AUTHORS_STORAGE,
      chunkId,
      filePath,
      async () => {
        const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
        if (!response.ok) throw new Error(`Failed to load author chunk ${chunkId}`)

        const buffer = new Uint8Array(await response.arrayBuffer())
        const bb = new flatbuffers.ByteBuffer(buffer)

        const chunkFile = AuthorChunkFile.getRootAsAuthorChunkFile(bb)
        const len = chunkFile.authorsLength()
        const authors: AuthorStats[] = new Array(len)
        let count = 0
        for (let i = 0; i < len; i++) {
          const author = chunkFile.authors(i)
          if (author) {
            authors[count++] = convertAuthor(author)
          }
        }
        authors.length = count

        return authors
      }
    )

    if (!result.data) {
      throw new Error(`Failed to load author chunk ${chunkId}: ${result.error || 'Unknown error'}`)
    }

    authorsCache.value.set(chunkId, result.data)

    if (!loadedAuthorChunkIds.value.includes(chunkId)) {
      loadedAuthorChunkIds.value.push(chunkId)
      await setMetadata(AUTHORS_STORAGE, {
        loadedChunkIds: [...loadedAuthorChunkIds.value],
        totalChunks: totalChunks.value,
        version: STORAGE_VERSION
      })
    }

    return result.data
  }

  async function loadAllAuthors(progressCallback?: (loaded: number, total: number) => void): Promise<AuthorStats[]> {
    const index = await loadMetadata()
    const allAuthors: AuthorStats[] = []

    for (let i = 0; i < index.chunks.length; i++) {
      const chunkAuthors = await loadAuthorChunk(i)
      allAuthors.push(...chunkAuthors)
      
      if (progressCallback) {
        progressCallback(i + 1, index.chunks.length)
      }
    }

    return allAuthors
  }

  async function getAuthorByName(name: string): Promise<AuthorStats | null> {
    const index = await loadMetadata()

    for (const chunkInfo of index.chunks) {
      const authors = await loadAuthorChunk(chunkInfo.index)
      const found = authors.find(a => a.author === name)
      if (found) {
        return found
      }
    }

    return null
  }

  async function getAuthorsByChunk(chunkId: number): Promise<AuthorStats[]> {
    return loadAuthorChunk(chunkId)
  }

  function queryAuthors(
    filter?: AuthorFilter,
    page: number = 1,
    pageSize: number = 24
  ): {
    authors: AuthorStats[]
    total: number
    filteredTotal: number
    page: number
    pageSize: number
    hasMore: boolean
  } {
    const allAuthors = Array.from(authorsCache.value.values()).flat()

    let filtered = allAuthors

    if (filter?.minPoems !== undefined) {
      filtered = filtered.filter(a => a.poem_count >= filter.minPoems!)
    }

    if (filter?.maxPoems !== undefined) {
      filtered = filtered.filter(a => a.poem_count <= filter.maxPoems!)
    }

    if (filter?.search) {
      const searchLower = filter.search.toLowerCase()
      filtered = filtered.filter(a => a.author.toLowerCase().includes(searchLower))
    }

    filtered.sort((a, b) => b.poem_count - a.poem_count)

    const startIndex = (page - 1) * pageSize
    const paged = filtered.slice(startIndex, startIndex + pageSize)

    return {
      authors: paged,
      total: totalAuthors.value,
      filteredTotal: filtered.length,
      page,
      pageSize,
      hasMore: startIndex + pageSize < filtered.length
    }
  }

  async function getTopAuthors(limit: number = 20): Promise<AuthorStats[]> {
    const index = await loadMetadata()
    const allAuthors: AuthorStats[] = []

    for (let i = 0; i < Math.min(10, index.chunks.length); i++) {
      const chunkAuthors = await loadAuthorChunk(i)
      allAuthors.push(...chunkAuthors)
    }

    return allAuthors
      .sort((a, b) => b.poem_count - a.poem_count)
      .slice(0, limit)
  }

  async function getSimilarAuthors(authorName: string): Promise<Array<{ author: string; similarity: number }>> {
    const author = await getAuthorByName(authorName)
    return author?.similar_authors || []
  }

  async function getAuthorWordFrequency(authorName: string): Promise<Record<string, number>> {
    const author = await getAuthorByName(authorName)
    return author?.word_frequency || {}
  }

  async function getAuthorPoemTypes(authorName: string): Promise<Record<string, number>> {
    const author = await getAuthorByName(authorName)
    return author?.poem_type_counts || {}
  }

  function getLoadedAuthors(): AuthorStats[] {
    return Array.from(authorsCache.value.values()).flat()
  }

  async function preloadChunks(chunkIds: number[]): Promise<void> {
    await Promise.all(chunkIds.map(id => loadAuthorChunk(id)))
  }

  async function clearCache(): Promise<void> {
    authorsCache.value.clear()
    loadedAuthorChunkIds.value = []
  }

  return {
    metadata: authorsIndex,
    totalAuthors,
    totalChunks,
    loadedChunkCount,
    loading,
    error,
    loadMetadata,
    loadAuthorChunk,
    loadAllAuthors,
    getAuthorByName,
    getAuthorsByChunk,
    queryAuthors,
    getTopAuthors,
    getSimilarAuthors,
    getAuthorWordFrequency,
    getAuthorPoemTypes,
    getLoadedAuthors,
    preloadChunks,
    clearCache
  }
}
