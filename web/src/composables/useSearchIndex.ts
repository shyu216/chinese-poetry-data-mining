/**
 * @overview
 * file: web/src/composables/useSearchIndex.ts
 * category: pipeline / search
 * tech: Vue 3 + TypeScript
 * summary: 基于 poem_index 的二级索引检索层。通过按前缀分片的 index 文件（poem_index/*.json）实现快速按 ID 查询与关键词搜索。
 *
 * Data pipeline:
 *  - 元数据: 通过 `usePoemIndexManifest()` 加载 poem index manifest（包含 prefix -> filename 映射）
 *  - 分片加载: `loadPoemChunk(prefix)` 使用 `getVerifiedChunk` 加载并缓存每个 prefix 对应的 JSON 映射（id -> PoemSummary）
 *  - 查询: 通过前缀定位后在内存 Map 中查找（O(1)），或对所有已加载分片顺序扫描进行关键词搜索（O(n)）
 *  - 输出: 提供按 ID 查询、批量查询、关键词搜索、按作者/朝代分页等方法
 *
 * Complexity & cost:
 *  - 加载单个分片为 O(p)（p = 分片内诗词数量）
 *  - 按 ID 查询在已加载分片中为 O(1)
 *  - 全量关键词搜索为 O(total_poems)（避免在主线程频繁触发全量扫描）
 *  - 空间: 已加载分片占用 O(loaded_poems)，使用 Map 有利于快速查找但占用额外内存
 *
 * Exports / responsibilities:
 *  - `useSearchIndex()` -> `loadPoemChunk`, `searchPoemById`, `getPoemSummariesByIds`, `searchByKeyword`, `searchPoems`, `getPoemsByAuthor`, `clearCache`, 等接口
 *
 * Potential issues & recommendations:
 *  - 主线程扫描：关键词搜索在未使用索引时会扫描多个分片，建议对热点字段建立更小的倒排索引或在 Worker 中执行搜索。
 *  - 并发/节流：避免同时触发大量分片加载，可限制并发数并实现请求合并。
 *  - 持久化：已加载分片可序列化到 IndexedDB 以加速后续访问，但需注意版本/哈希校验以防过期数据。
 */
import { ref, shallowRef, computed, type Ref } from 'vue'
import type { SearchResult, SearchOptions, SearchResultSet, PoemIndexManifest, PoemSummary } from './types'
import { usePoemIndexManifest, POEM_INDEX_STORAGE } from './useMetadataLoader'
import { getCache, setCache, getMetadata, setMetadata, getValidatedMetadata } from './useCache'
import { getVerifiedChunk } from './useVerifiedCache'

/** 存储版本号 */
const STORAGE_VERSION = 1

const manifestCache = shallowRef<PoemIndexManifest | null>(null)
const poemChunkCache = shallowRef<Map<string, Map<string, PoemSummary>>>(new Map())
const loadedPrefixes: Ref<Set<string>> = ref(new Set())
const loadingPromises = new Map<string, Promise<any>>()

async function initLoadedPrefixes() {
  // 使用版本验证获取元数据
  const meta = await getValidatedMetadata(POEM_INDEX_STORAGE, STORAGE_VERSION, { autoClean: true })
  const prefixes = await getCache<string[]>(POEM_INDEX_STORAGE, 'loaded-prefixes')
  if (prefixes && meta) {
    loadedPrefixes.value = new Set(prefixes)
  } else {
    loadedPrefixes.value = new Set()
  }
}
initLoadedPrefixes()

export function useSearchIndex() {
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

    const manifestData = await loadMetadata()
    const fileName = manifestData.prefixMap[prefix]
    if (!fileName) return null

    const filePath = `poem_index/${fileName}`

    const result = await getVerifiedChunk<Record<string, PoemSummary>>(
      POEM_INDEX_STORAGE,
      prefix,
      filePath,
      async () => {
        const response = await fetch(`${import.meta.env.BASE_URL}data/${filePath}`)
        if (!response.ok) throw new Error(`Failed to load poem chunk ${prefix}`)
        return response.json()
      }
    )

    if (!result.data) {
      console.warn(`[useSearchIndex] Failed to load chunk ${prefix}: ${result.error || 'Unknown error'}`)
      return null
    }

    const poemMap = new Map<string, PoemSummary>()
    for (const [id, poem] of Object.entries(result.data)) {
      poemMap.set(id, poem as PoemSummary)
    }

    poemChunkCache.value.set(prefix, poemMap)
    loadedPrefixes.value.add(prefix)

    const prefixesArray = [...loadedPrefixes.value]
    await setCache(POEM_INDEX_STORAGE, 'loaded-prefixes', prefixesArray)

    await setMetadata(POEM_INDEX_STORAGE, {
      loadedChunkIds: prefixesArray.map(p => p.charCodeAt(0)),
      totalChunks: Object.keys(manifestData.prefixMap).length,
      version: STORAGE_VERSION
    })

    return poemMap
  }

  async function searchPoemById(id: string): Promise<PoemSummary | null> {
    const prefix = getPrefixFromId(id)
    const chunk = await loadPoemChunk(prefix)
    return chunk?.get(id) || null
  }

  /**
   * 根据诗词ID获取诗词摘要信息（包含chunk_id）
   * 这个函数优先使用 poem_index，它比 poems CSV chunk 更快
   */
  async function getPoemSummaryById(id: string): Promise<PoemSummary | null> {
    return searchPoemById(id)
  }

  /**
   * 批量获取诗词摘要信息，返回包含 chunk_id 的信息
   * 用于优化诗词详情加载（可以直接知道去哪个chunk加载详情）
   */
  async function getPoemSummariesByIds(ids: string[]): Promise<Map<string, PoemSummary>> {
    const result = new Map<string, PoemSummary>()
    
    // 按 prefix 分组，减少文件加载次数
    const idsByPrefix = new Map<string, string[]>()
    
    for (const id of ids) {
      const prefix = getPrefixFromId(id)
      if (!idsByPrefix.has(prefix)) {
        idsByPrefix.set(prefix, [])
      }
      idsByPrefix.get(prefix)!.push(id)
    }
    
    // 并行加载所有需要的 prefix chunks
    const loadPromises = Array.from(idsByPrefix.entries()).map(async ([prefix, prefixIds]) => {
      const chunk = await loadPoemChunk(prefix)
      if (chunk) {
        for (const id of prefixIds) {
          const poem = chunk.get(id)
          if (poem) {
            result.set(id, poem)
          }
        }
      }
    })
    
    await Promise.all(loadPromises)
    return result
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
    getPoemSummaryById,
    getPoemSummariesByIds,
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
