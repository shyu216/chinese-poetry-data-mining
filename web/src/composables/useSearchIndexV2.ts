import { ref, shallowRef, computed, type Ref } from 'vue'
import type { SearchResult, SearchOptions, SearchResultSet, PoemIndexManifest, PoemSummary } from './types'
import { usePoemIndexManifest, POEM_INDEX_STORAGE } from './useMetadataLoader'
import { getCache, setCache, getChunkedCache, setChunkedCache, getMetadata, setMetadata } from './useCacheV2'

const manifestCache = shallowRef<PoemIndexManifest | null>(null)
const poemChunkCache = shallowRef<Map<string, Map<string, PoemSummary>>>(new Map())
const loadedPrefixes: Ref<Set<string>> = ref(new Set())

async function initLoadedPrefixes() {
  const prefixes = await getCache<string[]>(POEM_INDEX_STORAGE, 'loaded-prefixes')
  if (prefixes) {
    loadedPrefixes.value = new Set(prefixes)
  }
}
initLoadedPrefixes()

export function useSearchIndexV2() {
  const { metadata: manifest, loading, error, loadMetadata } = usePoemIndexManifest()

  const totalPoems = computed(() => manifest.value?.metadata?.total || 0)
  const totalIndexFiles = computed(() => manifest.value?.metadata?.indexFiles || 0)

  function getPrefixFromId(id: string): string {
    return id.substring(0, 2).toLowerCase()
  }

  async function loadPoemChunk(prefix: string): Promise<Map<string, PoemSummary> | null> {
    if (poemChunkCache.value.has(prefix)) {
      return poemChunkCache.value.get(prefix)!
    }

    const cached = await getChunkedCache<Record<string, PoemSummary>>(POEM_INDEX_STORAGE, prefix)
    if (cached) {
      const map = new Map(Object.entries(cached))
      poemChunkCache.value.set(prefix, map)
      loadedPrefixes.value.add(prefix)
      return map
    }

    const manifestData = await loadMetadata()
    const fileName = manifestData.prefixMap[prefix]
    if (!fileName) return null

    const response = await fetch(`${import.meta.env.BASE_URL}data/poem_index/${fileName}`)
    if (!response.ok) return null

    const data = await response.json()

    const poemMap = new Map<string, PoemSummary>()
    for (const [id, poem] of Object.entries(data)) {
      poemMap.set(id, poem as PoemSummary)
    }

    poemChunkCache.value.set(prefix, poemMap)
    loadedPrefixes.value.add(prefix)

    await setChunkedCache(POEM_INDEX_STORAGE, prefix, data)

    const manifestDataForMeta = await loadMetadata()
    const prefixesArray = [...loadedPrefixes.value]
    await setCache(POEM_INDEX_STORAGE, 'loaded-prefixes', prefixesArray)

    return poemMap
  }

  async function searchPoemById(id: string): Promise<PoemSummary | null> {
    const prefix = getPrefixFromId(id)
    const chunk = await loadPoemChunk(prefix)
    return chunk?.get(id) || null
  }

  async function searchByKeyword(
    keyword: string,
    options?: {
      dynasty?: string
      genre?: string
      limit?: number
    }
  ): Promise<SearchResult[]> {
    const results: SearchResult[] = []
    const manifestData = await loadMetadata()
    const limit = options?.limit || 50

    const prefixes = Object.keys(manifestData.prefixMap)

    for (const prefix of prefixes) {
      if (results.length >= limit) break

      const chunk = await loadPoemChunk(prefix)
      if (!chunk) continue

      const keywordLower = keyword.toLowerCase()

      for (const [id, poem] of chunk.entries()) {
        if (results.length >= limit) break

        if (
          poem.title.toLowerCase().includes(keywordLower) ||
          poem.author.toLowerCase().includes(keywordLower) ||
          id.includes(keyword)
        ) {
          if (options?.dynasty && poem.dynasty !== options.dynasty) continue
          if (options?.genre && poem.genre !== options.genre) continue

          let score = 0
          if (poem.title.toLowerCase().includes(keywordLower)) score += 10
          if (poem.author.toLowerCase().includes(keywordLower)) score += 5
          if (id.includes(keyword)) score += 3

          results.push({
            id,
            title: poem.title,
            author: poem.author,
            dynasty: poem.dynasty,
            score
          })
        }
      }
    }

    return results.sort((a, b) => b.score - a.score)
  }

  async function searchPoems(
    query: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<SearchResultSet> {
    const results = await searchByKeyword(query, { limit: page * pageSize })

    const startIndex = (page - 1) * pageSize
    const pagedResults = results.slice(startIndex, startIndex + pageSize)

    return {
      results: pagedResults,
      total: results.length,
      page,
      pageSize,
      hasMore: startIndex + pageSize < results.length
    }
  }

  async function searchMultipleKeywords(
    keywords: string[],
    options?: {
      matchAll?: boolean
      dynasty?: string
      genre?: string
    }
  ): Promise<SearchResult[]> {
    const allResults: Map<string, SearchResult> = new Map()
    const limit = 100

    for (const keyword of keywords) {
      const results = await searchByKeyword(keyword, { 
        limit, 
        dynasty: options?.dynasty, 
        genre: options?.genre 
      })

      for (const result of results) {
        if (options?.matchAll) {
          if (!allResults.has(result.id)) {
            allResults.set(result.id, { ...result, score: 0 })
          }
          const existing = allResults.get(result.id)!
          existing.score += result.score
        } else {
          if (!allResults.has(result.id)) {
            allResults.set(result.id, result)
          }
        }
      }
    }

    return Array.from(allResults.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
  }

  async function getPoemsByPrefix(
    prefix: string,
    limit?: number
  ): Promise<PoemSummary[]> {
    const chunk = await loadPoemChunk(prefix)
    if (!chunk) return []

    const poems = Array.from(chunk.values())
    return limit ? poems.slice(0, limit) : poems
  }

  async function getPoemsByAuthor(
    author: string,
    limit: number = 50
  ): Promise<SearchResult[]> {
    const manifestData = await loadMetadata()
    const results: SearchResult[] = []

    const prefixes = Object.keys(manifestData.prefixMap)

    for (const prefix of prefixes) {
      if (results.length >= limit) break

      const chunk = await loadPoemChunk(prefix)
      if (!chunk) continue

      for (const [id, poem] of chunk.entries()) {
        if (results.length >= limit) break

        if (poem.author === author) {
          results.push({
            id,
            title: poem.title,
            author: poem.author,
            dynasty: poem.dynasty,
            score: 1
          })
        }
      }
    }

    return results
  }

  async function getPoemsByDynasty(
    dynasty: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<SearchResultSet> {
    const manifestData = await loadMetadata()
    const results: SearchResult[] = []

    const prefixes = Object.keys(manifestData.prefixMap)

    for (const prefix of prefixes) {
      const chunk = await loadPoemChunk(prefix)
      if (!chunk) continue

      for (const [id, poem] of chunk.entries()) {
        if (poem.dynasty === dynasty) {
          results.push({
            id,
            title: poem.title,
            author: poem.author,
            dynasty: poem.dynasty,
            score: 1
          })
        }
      }
    }

    const startIndex = (page - 1) * pageSize
    const pagedResults = results.slice(startIndex, startIndex + pageSize)

    return {
      results: pagedResults,
      total: results.length,
      page,
      pageSize,
      hasMore: startIndex + pageSize < results.length
    }
  }

  function getLoadedPrefixCount(): number {
    return loadedPrefixes.value.size
  }

  async function preloadPrefixes(prefixes: string[]): Promise<void> {
    await Promise.all(prefixes.map(p => loadPoemChunk(p)))
  }

  async function clearCache(): Promise<void> {
    poemChunkCache.value.clear()
    loadedPrefixes.value = new Set()
  }

  return {
    metadata: manifest,
    totalPoems,
    totalIndexFiles,
    loadedPrefixCount: computed(() => loadedPrefixes.value.size),
    loading,
    error,
    loadMetadata,
    loadPoemChunk,
    searchPoemById,
    searchByKeyword,
    searchPoems,
    searchMultipleKeywords,
    getPoemsByPrefix,
    getPoemsByAuthor,
    getPoemsByDynasty,
    getLoadedPrefixCount,
    preloadPrefixes,
    clearCache
  }
}
