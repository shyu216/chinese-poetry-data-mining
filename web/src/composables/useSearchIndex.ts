import { ref, shallowRef } from 'vue'

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

const poemsCache = shallowRef<Map<string, PoemSummary>>(new Map())
const loading = ref(false)

export function useSearchIndex() {
  const loadPoems = async (): Promise<Map<string, PoemSummary>> => {
    if (poemsCache.value.size > 0) return poemsCache.value

    loading.value = true
    try {
      const response = await fetch('/data/poems/summary.json')
      const data: PoemsSummary = await response.json()
      
      const map = new Map<string, PoemSummary>()
      for (const poem of data.poems) {
        map.set(poem.id, poem)
      }
      poemsCache.value = map
      console.log(`Loaded ${map.size} poems`)
      return map
    } finally {
      loading.value = false
    }
  }

  const loadKeywordIndex = async (indexNum: number): Promise<Record<string, string[]>> => {
    const key = `keyword_${indexNum.toString().padStart(4, '0')}`
    
    try {
      const response = await fetch(`/data/keyword_index/${key}.json`)
      if (!response.ok) return {}
      const data = await response.json()
      return data
    } catch {
      return {}
    }
  }

  const getRandomKeywordIndex = async (): Promise<{ keyword: string; poems: SearchResult[] }> => {
    const poems = await loadPoems()
    
    const indexNum = Math.floor(Math.random() * 2000)
    console.log(`Loading keyword index ${indexNum}...`)
    const keywordData = await loadKeywordIndex(indexNum)
    
    const keywords = Object.keys(keywordData)
    if (keywords.length === 0) {
      return { keyword: '', poems: [] }
    }
    
    const randomKeyword = keywords[Math.floor(Math.random() * keywords.length)]
    const poemIds = keywordData[randomKeyword] || []
    
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
    
    console.log(`Keyword: ${randomKeyword}, Found ${results.length} poems`)
    return { keyword: randomKeyword, poems: results }
  }

  const searchByKeyword = async (keyword: string): Promise<SearchResult[]> => {
    const poems = await loadPoems()
    
    for (let i = 0; i < 204; i++) {
      const key = `keyword_${i.toString().padStart(4, '0')}`
      
      try {
        const response = await fetch(`/data/keyword_index/${key}.json`)
        if (!response.ok) continue
        const keywordData: Record<string, string[]> = await response.json()
        
        if (keywordData[keyword]) {
          const poemIds = keywordData[keyword]
          const results: SearchResult[] = []
          
          for (const id of poemIds.slice(0, 50)) {
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
          return results
        }
      } catch {
        continue
      }
    }
    
    return []
  }

  return {
    getRandomKeywordIndex,
    searchByKeyword,
    loadPoems,
    loading
  }
}
