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

interface PoemsSummary {
  metadata: { total: number }
  poems: PoemSummary[]
}

interface KeywordIndex {
  [keyword: string]: string[]
}

const poemsCache = shallowRef<Map<string, PoemSummary>>(new Map())
const keywordCache = shallowRef<Map<number, KeywordIndex>>(new Map())
const loading = ref(false)
const initialized = ref(false)

export function useSearchIndex() {
  const loadPoems = async (): Promise<Map<string, PoemSummary>> => {
    if (poemsCache.value.size > 0) return poemsCache.value

    loading.value = true
    try {
      const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/summary.json`)
      const data: PoemsSummary = await response.json()
      
      const map = new Map<string, PoemSummary>()
      for (const poem of data.poems) {
        map.set(poem.id, poem)
      }
      poemsCache.value = map
      initialized.value = true
      console.log(`[useSearchIndex] Loaded ${map.size} poems`)
      return map
    } catch (error) {
      console.error('[useSearchIndex] Failed to load poems:', error)
      return new Map()
    } finally {
      loading.value = false
    }
  }

  const loadKeywordIndex = async (indexNum: number): Promise<KeywordIndex | null> => {
    if (keywordCache.value.has(indexNum)) {
      return keywordCache.value.get(indexNum)!
    }
    
    const key = `keyword_${indexNum.toString().padStart(4, '0')}`
    
    try {
      const response = await fetch(`/data/keyword_index/${key}.json`)
      if (!response.ok) return null
      const data: KeywordIndex = await response.json()
      
      keywordCache.value.set(indexNum, data)
      return data
    } catch {
      return null
    }
  }

  const preloadKeywordIndices = async (indices: number[] = [0, 1, 2, 3, 4]) => {
    const promises = indices.map(i => loadKeywordIndex(i))
    await Promise.allSettled(promises)
  }

  const getRandomKeywordIndex = async (): Promise<{ keyword: string; poems: SearchResult[]; totalMatches: number }> => {
    const poems = await loadPoems()
    
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
    
    const results: SearchResult[] = []
    for (const id of poemIds.slice(0, 20)) {
      const poem = poems.get(id)
      if (poem) {
        results.push({
          id: poem.id,
          title: poem.title || '无题',
          author: poem.author,
          dynasty: poem.dynasty,
          score: 5
        })
      }
    }
    
    return { 
      keyword: randomKeyword, 
      poems: results,
      totalMatches: poemIds.length
    }
  }

  const searchByKeyword = async (keyword: string): Promise<SearchResult[]> => {
    if (!keyword.trim()) return []
    
    const poems = await loadPoems()
    const results: SearchResult[] = []
    const seenIds = new Set<string>()
    
    const charCode = keyword.charCodeAt(0)
    let startIndex = 0
    if (charCode >= 0x4E00 && charCode <= 0x9FFF) {
      startIndex = Math.floor(Math.random() * 150)
    }
    
    for (let i = startIndex; i < startIndex + 50; i++) {
      const indexNum = i % 200
      const keywordData = await loadKeywordIndex(indexNum)
      
      if (!keywordData) continue
      
      if (keyword in keywordData) {
        const poemIds = keywordData[keyword] || []
        for (const id of poemIds.slice(0, 30)) {
          if (!seenIds.has(id)) {
            seenIds.add(id)
            const poem = poems.get(id)
            if (poem) {
              results.push({
                id: poem.id,
                title: poem.title || '无题',
                author: poem.author,
                dynasty: poem.dynasty,
                score: 5
              })
            }
          }
        }
        
        if (results.length >= 50) break
      }
    }
    
    console.log(`[useSearchIndex] Search "${keyword}": found ${results.length} poems`)
    return results
  }

  const getPoemById = async (id: string): Promise<PoemSummary | null> => {
    const poems = await loadPoems()
    return poems.get(id) || null
  }

  return {
    loading,
    initialized,
    loadPoems,
    loadKeywordIndex,
    preloadKeywordIndices,
    getRandomKeywordIndex,
    searchByKeyword,
    getPoemById
  }
}
