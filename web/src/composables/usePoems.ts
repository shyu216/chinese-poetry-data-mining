import { ref, shallowRef } from 'vue'
import type { PoemSummary } from './useSearchIndex'

interface PoemsData {
  metadata: { total: number; chunks: number }
  poems: PoemSummary[]
}

const poemsCache = shallowRef<PoemsData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

export function usePoems() {
  const loadSummary = async (): Promise<PoemsData> => {
    if (poemsCache.value) return poemsCache.value

    loading.value = true
    error.value = null

    try {
      const response = await fetch('/data/poems/summary.json')
      if (!response.ok) throw new Error('Failed to load poems summary')
      const data = await response.json()
      poemsCache.value = data
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      throw e
    } finally {
      loading.value = false
    }
  }

  const getPoemsByAuthor = async (author: string): Promise<PoemSummary[]> => {
    const data = await loadSummary()
    return data.poems.filter(p => p.author === author)
  }

  const getPoemsByDynasty = async (dynasty: string): Promise<PoemSummary[]> => {
    const data = await loadSummary()
    return data.poems.filter(p => p.dynasty === dynasty)
  }

  const getPoemsByGenre = async (genre: string): Promise<PoemSummary[]> => {
    const data = await loadSummary()
    return data.poems.filter(p => p.genre === genre)
  }

  const getPoemById = async (id: string): Promise<PoemSummary | null> => {
    const data = await loadSummary()
    return data.poems.find(p => p.id === id) || null
  }

  return {
    loadSummary,
    getPoemsByAuthor,
    getPoemsByDynasty,
    getPoemsByGenre,
    getPoemById,
    loading,
    error
  }
}
