import { ref, shallowRef } from 'vue'

export interface Author {
  dynasty: string
  poem_count: number
  genres: string[]
}

interface AuthorsIndex {
  metadata: { total_authors: number }
  authors: Record<string, Author>
}

const authorsCache = shallowRef<AuthorsIndex | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

export function useAuthors() {
  const loadAuthors = async (): Promise<AuthorsIndex> => {
    if (authorsCache.value) return authorsCache.value

    loading.value = true
    error.value = null

    try {
      const response = await fetch('/data/poems/author_index.json')
      if (!response.ok) throw new Error('Failed to load authors index')
      const data = await response.json()
      authorsCache.value = data
      return data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
      throw e
    } finally {
      loading.value = false
    }
  }

  const getAuthor = async (name: string): Promise<Author | null> => {
    const authors = await loadAuthors()
    return authors.authors[name] || null
  }

  const getTopAuthors = async (limit: number = 50): Promise<Array<{ name: string } & Author>> => {
    const authors = await loadAuthors()
    return Object.entries(authors.authors)
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.poem_count - a.poem_count)
      .slice(0, limit)
  }

  const getAuthorsByDynasty = async (dynasty: string): Promise<Array<{ name: string } & Author>> => {
    const authors = await loadAuthors()
    return Object.entries(authors.authors)
      .filter(([_, data]) => data.dynasty === dynasty)
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.poem_count - a.poem_count)
  }

  return {
    loadAuthors,
    getAuthor,
    getTopAuthors,
    getAuthorsByDynasty,
    loading,
    error
  }
}
