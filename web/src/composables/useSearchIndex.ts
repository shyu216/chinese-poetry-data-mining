import { ref, shallowRef, computed, onUnmounted } from 'vue'

export interface SearchResult {
  id: string
  title: string
  author: string
  dynasty: string
  score: number
}

export interface PoemSummary {
  id: string
  title: string
  author: string
  dynasty: string
  genre: string
  poem_type: string
  meter_pattern: string
}

interface Manifest {
  metadata: {
    total: number
    chunks: number
    indexFiles: number
    prefixLength: number
    generatedAt: string
  }
  prefixMap: { [prefix: string]: string }
}

interface KeywordIndex {
  [keyword: string]: string[]
}

// 分块缓存 - 只缓存已加载的分块
const poemChunkCache = shallowRef<Map<string, Map<string, PoemSummary>>>(new Map())
const keywordCache = shallowRef<Map<number, KeywordIndex>>(new Map())
const manifestCache = shallowRef<Manifest | null>(null)
const loading = ref(false)
const initialized = ref(false)

// 获取诗歌 ID 对应的分块前缀
function getPrefixFromId(id: string): string {
  return id.substring(0, 2).toLowerCase()
}

export function useSearchIndex() {
  // 加载 manifest 文件
  const loadManifest = async (): Promise<Manifest | null> => {
    if (manifestCache.value) return manifestCache.value

    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/poem_index/poem_index_manifest.json`)
      if (!response.ok) return null
      const data: Manifest = await response.json()
      manifestCache.value = data
      console.log(`[useSearchIndex] Loaded manifest: ${data.metadata.total} poems, ${data.metadata.indexFiles} index files`)
      return data
    } catch (error) {
      console.error('[useSearchIndex] Failed to load manifest:', error)
      return null
    }
  }

  // 按需加载诗歌分块
  const loadPoemChunk = async (prefix: string): Promise<Map<string, PoemSummary> | null> => {
    // 检查缓存
    if (poemChunkCache.value.has(prefix)) {
      return poemChunkCache.value.get(prefix)!
    }

    const manifest = await loadManifest()
    if (!manifest) return null

    const fileName = manifest.prefixMap[prefix]
    if (!fileName) return null

    loading.value = true
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/poem_index/${fileName}`)
      if (!response.ok) return null

      const data: { [id: string]: PoemSummary } = await response.json()

      // 转换为 Map
      const map = new Map<string, PoemSummary>()
      for (const [id, poem] of Object.entries(data)) {
        map.set(id, poem)
      }

      // 存入缓存
      poemChunkCache.value.set(prefix, map)
      initialized.value = true

      console.log(`[useSearchIndex] Loaded poem chunk ${prefix}: ${map.size} poems`)
      return map
    } catch (error) {
      console.error(`[useSearchIndex] Failed to load poem chunk ${prefix}:`, error)
      return null
    } finally {
      loading.value = false
    }
  }

  // 获取诗歌（自动加载对应分块）
  const getPoemById = async (id: string): Promise<PoemSummary | null> => {
    const prefix = getPrefixFromId(id)
    const chunk = await loadPoemChunk(prefix)
    return chunk?.get(id) || null
  }

  // 批量获取诗歌（优化：相同分块的只加载一次）
  const getPoemsByIds = async (ids: string[]): Promise<Map<string, PoemSummary>> => {
    const result = new Map<string, PoemSummary>()

    // 按前缀分组
    const idsByPrefix = new Map<string, string[]>()
    for (const id of ids) {
      const prefix = getPrefixFromId(id)
      if (!idsByPrefix.has(prefix)) {
        idsByPrefix.set(prefix, [])
      }
      idsByPrefix.get(prefix)!.push(id)
    }

    // 并行加载所有需要的分块
    const promises = Array.from(idsByPrefix.entries()).map(async ([prefix, prefixIds]) => {
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

    await Promise.all(promises)
    return result
  }

  // 加载关键词索引（保持原有逻辑）
  const loadKeywordIndex = async (indexNum: number): Promise<KeywordIndex | null> => {
    if (keywordCache.value.has(indexNum)) {
      return keywordCache.value.get(indexNum)!
    }

    const key = `keyword_${indexNum.toString().padStart(4, '0')}`

    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/keyword_index/${key}.json`)
      if (!response.ok) return null
      const data: KeywordIndex = await response.json()

      keywordCache.value.set(indexNum, data)
      return data
    } catch {
      return null
    }
  }

  // 预加载关键词索引（保持原有逻辑）
  const preloadKeywordIndices = async (indices: number[] = [0, 1, 2, 3, 4]) => {
    const promises = indices.map(i => loadKeywordIndex(i))
    await Promise.allSettled(promises)
  }

  // 获取随机关键词（更新为使用新的诗歌获取方式）
  const getRandomKeywordIndex = async (): Promise<{ keyword: string; poems: SearchResult[]; totalMatches: number }> => {
    const indexNum = Math.floor(Math.random() * 200)
    const keywordData = await loadKeywordIndex(indexNum)

    if (!keywordData) {
      return { keyword: '', poems: [], totalMatches: 0 }
    }

    const keywords = Object.keys(keywordData)
    if (keywords.length === 0) {
      return { keyword: '', poems: [], totalMatches: 0 }
    }

    const randomKeyword = keywords[Math.floor(Math.random() * keywords.length)] || ''
    const poemIds = randomKeyword ? (keywordData[randomKeyword] || []) : []

    // 使用批量获取
    const poems = await getPoemsByIds(poemIds.slice(0, 20))

    const results: SearchResult[] = []
    for (const [id, poem] of poems) {
      results.push({
        id: poem.id,
        title: poem.title || '无题',
        author: poem.author,
        dynasty: poem.dynasty,
        score: 5
      })
    }

    return {
      keyword: randomKeyword,
      poems: results,
      totalMatches: poemIds.length
    }
  }

  // 关键词搜索（更新为使用新的诗歌获取方式）
  const searchByKeyword = async (keyword: string): Promise<SearchResult[]> => {
    if (!keyword.trim()) return []

    const results: SearchResult[] = []
    const seenIds = new Set<string>()
    const idsToFetch: string[] = []

    const charCode = keyword.charCodeAt(0)
    let startIndex = 0
    if (charCode >= 0x4E00 && charCode <= 0x9FFF) {
      startIndex = Math.floor(Math.random() * 150)
    }

    // 先收集所有匹配的 ID
    for (let i = startIndex; i < startIndex + 50; i++) {
      const indexNum = i % 200
      const keywordData = await loadKeywordIndex(indexNum)

      if (!keywordData) continue

      if (keyword in keywordData) {
        const poemIds = keywordData[keyword] || []
        for (const id of poemIds.slice(0, 30)) {
          if (!seenIds.has(id)) {
            seenIds.add(id)
            idsToFetch.push(id)
          }
        }

        if (idsToFetch.length >= 50) break
      }
    }

    // 批量获取诗歌详情
    const poems = await getPoemsByIds(idsToFetch.slice(0, 50))

    for (const [id, poem] of poems) {
      results.push({
        id: poem.id,
        title: poem.title || '无题',
        author: poem.author,
        dynasty: poem.dynasty,
        score: 5
      })
    }

    console.log(`[useSearchIndex] Search "${keyword}": found ${results.length} poems`)
    return results
  }

  // 预加载常用分块（可选优化）
  const preloadCommonChunks = async (prefixes: string[] = ['08', '0a', '0b', '0c', '0d']) => {
    const promises = prefixes.map(p => loadPoemChunk(p))
    await Promise.allSettled(promises)
  }

  // 获取缓存统计
  const getCacheStats = () => {
    return {
      poemChunks: poemChunkCache.value.size,
      keywordIndices: keywordCache.value.size,
      totalCachedPoems: Array.from(poemChunkCache.value.values())
        .reduce((sum, chunk) => sum + chunk.size, 0)
    }
  }

  return {
    loading,
    initialized,
    loadManifest,
    loadPoemChunk,
    getPoemById,
    getPoemsByIds,
    loadKeywordIndex,
    preloadKeywordIndices,
    preloadCommonChunks,
    getRandomKeywordIndex,
    searchByKeyword,
    getCacheStats
  }
}
