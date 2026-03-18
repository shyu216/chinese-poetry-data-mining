import { ref, shallowRef, computed, type Ref, type ShallowRef } from 'vue'
import type {
  PoemsIndex,
  AuthorsIndex,
  WordCountMeta,
  WordSimilarityMetadata,
  PoemIndexManifest
} from './types'
import { getCache, setCache, getChunkedCache, setChunkedCache } from './useCacheV2'

export type MetadataType = 'poems' | 'authors' | 'wordcount' | 'wordSimilarity' | 'poemIndex'

export interface MetadataConfig {
  type: MetadataType
  storageName: string
  url: string
  fallback?: () => Promise<unknown>
}

const metadataConfigs: Record<MetadataType, Omit<MetadataConfig, 'type'>> = {
  poems: {
    storageName: 'poems-index',
    url: 'data/preprocessed/poems_chunk_meta.json'
  },
  authors: {
    storageName: 'authors-index',
    url: 'data/author_v2/authors-meta.json'
  },
  wordcount: {
    storageName: 'wordcount-meta',
    url: 'data/wordcount_v2/meta.json'
  },
  wordSimilarity: {
    storageName: 'word-similarity-meta',
    url: 'data/word_similarity_v3/metadata.json'
  },
  poemIndex: {
    storageName: 'poem-index-manifest',
    url: 'data/poem_index/poem_index_manifest.json'
  }
}

const metadataCache = ref<Record<MetadataType, unknown>>({
  poems: undefined,
  authors: undefined,
  wordcount: undefined,
  wordSimilarity: undefined,
  poemIndex: undefined
})
const loadingStates: Map<MetadataType, Ref<boolean>> = new Map()
const errorStates: Map<MetadataType, Ref<string | null>> = new Map()

function getOrCreateStates(type: MetadataType) {
  if (!loadingStates.has(type)) {
    loadingStates.set(type, ref(false))
    errorStates.set(type, ref(null))
  }
  return {
    loading: loadingStates.get(type)!,
    error: errorStates.get(type)!
  }
}

export function useMetadataLoader<T = unknown>(type: MetadataType) {
  const config = metadataConfigs[type]
  const { loading, error } = getOrCreateStates(type)

  const metadata = computed(() => metadataCache.value[type] as T | undefined)

  async function loadMetadata(forceRefresh = false): Promise<T> {
    if (metadata.value && !forceRefresh) {
      return metadata.value
    }

    loading.value = true
    error.value = null

    try {
      const cached = await getCache<T>(config.storageName, 'metadata')
      if (cached && !forceRefresh) {
        metadataCache.value = { ...metadataCache.value, [type]: cached }
        return cached
      }

      const response = await fetch(`${import.meta.env.BASE_URL}${config.url}`)
      if (!response.ok) {
        throw new Error(`Failed to load ${type} metadata: ${response.status}`)
      }

      const data: T = await response.json()

      await setCache(config.storageName, 'metadata', data)
      metadataCache.value = { ...metadataCache.value, [type]: data }

      return data
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Unknown error'

      if (config.fallback) {
        try {
          const fallbackData = await config.fallback() as T
          metadataCache.value = { ...metadataCache.value, [type]: fallbackData }
          return fallbackData
        } catch {
          error.value = errorMessage
          throw e
        }
      }

      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function clearMetadata(): Promise<void> {
    const newCache = { ...metadataCache.value }
    delete newCache[type]
    metadataCache.value = newCache
  }

  return {
    metadata,
    loading,
    error,
    loadMetadata,
    clearMetadata
  }
}

export function usePoemsMetadata() {
  return useMetadataLoader<PoemsIndex>('poems')
}

export function useAuthorsMetadata() {
  return useMetadataLoader<AuthorsIndex>('authors')
}

export function useWordcountMetadata() {
  return useMetadataLoader<WordCountMeta>('wordcount')
}

export function useWordSimilarityMetadata() {
  return useMetadataLoader<WordSimilarityMetadata>('wordSimilarity')
}

export function usePoemIndexManifest() {
  return useMetadataLoader<PoemIndexManifest>('poemIndex')
}

export const POEMS_STORAGE = 'poems-v2'
export const AUTHORS_STORAGE = 'authors-v2'
export const WORDCOUNT_STORAGE = 'wordcount-v2'
export const WORD_SIMILARITY_STORAGE = 'word-similarity-v2'
export const POEM_INDEX_STORAGE = 'poem-index-v2'
export const KEYWORD_INDEX_STORAGE = 'keyword-index-v2'

export function getChunkUrl(basePath: string, chunkId: number, padding = 4): string {
  const paddedId = chunkId.toString().padStart(padding, '0')
  return `${import.meta.env.BASE_URL}${basePath}_${paddedId}`
}

export function parseCsvLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  result.push(current.trim())
  return result
}
