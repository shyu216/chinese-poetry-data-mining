import { ref, shallowRef, computed, type Ref } from 'vue'
import * as flatbuffers from 'flatbuffers'
import type { AuthorStats, AuthorFilter, AuthorQueryResult, AuthorsIndex } from './types'
import { useAuthorsMetadata, AUTHORS_STORAGE } from './useMetadataLoader'
import { getChunkedCache, setChunkedCache, getMetadata, setMetadata } from './useCacheV2'

const authorsCache = shallowRef<Map<number, AuthorStats[]>>(new Map())
const loadedAuthorChunkIds: Ref<number[]> = ref([])

async function initLoadedAuthorChunkIds() {
  const meta = await getMetadata(AUTHORS_STORAGE)
  if (meta) {
    loadedAuthorChunkIds.value = meta.loadedChunkIds
  }
}
initLoadedAuthorChunkIds()

function convertWordFreq(wf: unknown): { word: string; count: number } {
  return {
    word: (wf as { word(): string }).word() || '',
    count: (wf as { count(): number }).count()
  }
}

function convertMeterPattern(mp: unknown): { pattern: string; count: number } {
  return {
    pattern: (mp as { pattern(): string }).pattern() || '',
    count: (mp as { count(): number }).count()
  }
}

function convertSimilarAuthor(sa: unknown): { author: string; similarity: number } {
  return {
    author: (sa as { author(): string }).author() || '',
    similarity: (sa as { similarity(): number }).similarity()
  }
}

function convertAuthor(author: unknown): AuthorStats {
  const a = author as {
    author(): string
    poemCount(): number
    poemIdsLength(): number
    poemIds(index: number): string | null
    poemTypeCountsLength(): number
    poemTypeCounts(index: number): unknown
    meterPatternsLength(): number
    meterPatterns(index: number): unknown
    wordFrequencyLength(): number
    wordFrequency(index: number): unknown
    similarAuthorsLength(): number
    similarAuthors(index: number): unknown
  }

  const poemTypeCounts: Record<string, number> = {}
  for (let i = 0; i < a.poemTypeCountsLength(); i++) {
    const wf = a.poemTypeCounts(i)
    if (wf) {
      const word = convertWordFreq(wf).word
      if (word) {
        poemTypeCounts[word] = convertWordFreq(wf).count
      }
    }
  }

  const meterPatterns: Array<{ pattern: string; count: number }> = []
  for (let i = 0; i < a.meterPatternsLength(); i++) {
    const mp = a.meterPatterns(i)
    if (mp) {
      meterPatterns.push(convertMeterPattern(mp))
    }
  }

  const wordFrequency: Record<string, number> = {}
  for (let i = 0; i < a.wordFrequencyLength(); i++) {
    const wf = a.wordFrequency(i)
    if (wf) {
      const word = convertWordFreq(wf).word
      if (word) {
        wordFrequency[word] = convertWordFreq(wf).count
      }
    }
  }

  const similarAuthors: Array<{ author: string; similarity: number }> = []
  for (let i = 0; i < a.similarAuthorsLength(); i++) {
    const sa = a.similarAuthors(i)
    if (sa) {
      similarAuthors.push(convertSimilarAuthor(sa))
    }
  }

  const poemIds: string[] = []
  for (let i = 0; i < a.poemIdsLength(); i++) {
    const id = a.poemIds(i)
    if (id) {
      poemIds.push(id)
    }
  }

  return {
    author: a.author() || '',
    poem_count: a.poemCount(),
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

    const cached = await getChunkedCache<AuthorStats[]>(AUTHORS_STORAGE, chunkId)
    if (cached) {
      authorsCache.value.set(chunkId, cached)
      return cached
    }

    const chunkIdStr = chunkId.toString().padStart(4, '0')
    const response = await fetch(`${import.meta.env.BASE_URL}data/author_v2/author_chunk_${chunkIdStr}.fbs`)
    if (!response.ok) throw new Error(`Failed to load author chunk ${chunkId}`)

    const buffer = new Uint8Array(await response.arrayBuffer())
    const bb = new flatbuffers.ByteBuffer(buffer)

    const chunkFile = (await import('@/generated/author-chunk/author-chunk-file')).AuthorChunkFile.getRootAsAuthorChunkFile(bb)
    const authors: AuthorStats[] = []

    for (let i = 0; i < chunkFile.authorsLength(); i++) {
      const author = chunkFile.authors(i)
      if (author) {
        authors.push(convertAuthor(author))
      }
    }

    authorsCache.value.set(chunkId, authors)
    await setChunkedCache(AUTHORS_STORAGE, chunkId, authors)

    if (!loadedAuthorChunkIds.value.includes(chunkId)) {
      loadedAuthorChunkIds.value.push(chunkId)
      await setMetadata(AUTHORS_STORAGE, { 
        loadedChunkIds: [...loadedAuthorChunkIds.value], 
        totalChunks: totalChunks.value 
      })
    }

    return authors
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
