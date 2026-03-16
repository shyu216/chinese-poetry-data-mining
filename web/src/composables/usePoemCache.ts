import { openDB, type DBSchema, type IDBPDatabase } from 'idb'
import type { PoemSummary, PoemDetail } from './usePoems'
import type { AuthorStats } from '@/types/author'
import type { WordSimilarityChunk } from './useWordSimilarityFbs'

interface PoemCacheSchema extends DBSchema {
  chunks: {
    key: number
    value: {
      id: number
      poems: PoemSummary[]
      timestamp: number
    }
  }
  chunkDetails: {
    key: number
    value: {
      id: number
      poems: [string, PoemDetail][]
      timestamp: number
    }
  }
  index: {
    key: string
    value: {
      key: string
      data: any
      timestamp: number
    }
  }
  metadata: {
    key: string
    value: {
      key: string
      loadedChunkIds: number[]
      timestamp: number
    }
  }
  authors: {
    key: string
    value: {
      key: string
      data: AuthorStats[]
      timestamp: number
    }
  }
  authorChunks: {
    key: number
    value: {
      id: number
      authors: AuthorStats[]
      timestamp: number
    }
  }
  authorMetadata: {
    key: string
    value: {
      key: string
      loadedChunkIds: number[]
      totalChunks: number
      timestamp: number
    }
  }
  wordSimilarityVocab: {
    key: string
    value: {
      key: string
      data: Record<string, number>
      timestamp: number
    }
  }
  wordSimilarityChunks: {
    key: number
    value: {
      id: number
      vocab: string[]
      entries: [number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }][]
      timestamp: number
    }
  }
}

const DB_NAME = 'poem-cache'
const DB_VERSION = 4

let dbPromise: Promise<IDBPDatabase<PoemCacheSchema>> | null = null

const getDB = () => {
  if (!dbPromise) {
    dbPromise = openDB<PoemCacheSchema>(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion) {
        if (oldVersion < 1) {
          db.createObjectStore('chunks', { keyPath: 'id' })
          db.createObjectStore('chunkDetails', { keyPath: 'id' })
          db.createObjectStore('index', { keyPath: 'key' })
          db.createObjectStore('metadata', { keyPath: 'key' })
        }
        if (oldVersion < 2) {
          db.createObjectStore('authors', { keyPath: 'key' })
        }
        if (oldVersion < 3) {
          db.createObjectStore('wordSimilarityVocab', { keyPath: 'key' })
          db.createObjectStore('wordSimilarityChunks', { keyPath: 'id' })
        }
        if (oldVersion < 4) {
          db.createObjectStore('authorChunks', { keyPath: 'id' })
          db.createObjectStore('authorMetadata', { keyPath: 'key' })
        }
      }
    })
  }
  return dbPromise
}

// Cache chunk summaries
export async function cacheChunkSummaries(chunkId: number, poems: PoemSummary[]) {
  const db = await getDB()
  await db.put('chunks', {
    id: chunkId,
    poems,
    timestamp: Date.now()
  })
}

// Get cached chunk summaries
export async function getCachedChunkSummaries(chunkId: number): Promise<PoemSummary[] | null> {
  const db = await getDB()
  const cached = await db.get('chunks', chunkId)
  return cached?.poems || null
}

// Cache chunk details
export async function cacheChunkDetails(chunkId: number, poems: Map<string, PoemDetail>) {
  const db = await getDB()
  // Convert Map to array for storage
  const poemsArray = Array.from(poems.entries())
  await db.put('chunkDetails', {
    id: chunkId,
    poems: poemsArray,
    timestamp: Date.now()
  })
}

// Get cached chunk details
export async function getCachedChunkDetails(chunkId: number): Promise<Map<string, PoemDetail> | null> {
  const db = await getDB()
  const cached = await db.get('chunkDetails', chunkId)
  if (!cached) return null
  // Convert array back to Map
  return new Map(cached.poems)
}

// Cache index
export async function cacheIndex(data: any) {
  const db = await getDB()
  await db.put('index', {
    key: 'main',
    data,
    timestamp: Date.now()
  })
}

// Get cached index
export async function getCachedIndex(): Promise<any | null> {
  const db = await getDB()
  const cached = await db.get('index', 'main')
  return cached?.data || null
}

// Cache metadata (loaded chunk IDs)
export async function cacheMetadata(loadedChunkIds: number[]) {
  const db = await getDB()
  await db.put('metadata', {
    key: 'session',
    loadedChunkIds,
    timestamp: Date.now()
  })
}

// Get cached metadata
export async function getCachedMetadata(): Promise<number[] | null> {
  const db = await getDB()
  const cached = await db.get('metadata', 'session')
  return cached?.loadedChunkIds || null
}

// Clear all cache
export async function clearCache() {
  const db = await getDB()
  await db.clear('chunks')
  await db.clear('chunkDetails')
  await db.clear('index')
  await db.clear('metadata')
}

// Get cache stats
export async function getCacheStats(): Promise<{
  chunks: number
  chunkDetails: number
  hasIndex: boolean
  loadedChunkIds: number
}> {
  const db = await getDB()
  const chunks = await db.count('chunks')
  const chunkDetails = await db.count('chunkDetails')
  const index = await db.get('index', 'main')
  const metadata = await db.get('metadata', 'session')
  return {
    chunks,
    chunkDetails,
    hasIndex: !!index,
    loadedChunkIds: metadata?.loadedChunkIds?.length || 0
  }
}

// Get detailed cache info for dashboard
export async function getCacheDetails(): Promise<{
  chunks: { id: number; count: number; timestamp: number }[]
  totalSize: number
}> {
  const db = await getDB()
  const allChunks = await db.getAll('chunks')
  
  const chunks = allChunks.map(c => ({
    id: c.id,
    count: c.poems.length,
    timestamp: c.timestamp
  }))
  
  // Estimate size (rough calculation)
  const totalSize = allChunks.reduce((sum, c) => {
    return sum + JSON.stringify(c).length * 2 // UTF-16 bytes
  }, 0)
  
  return { chunks, totalSize }
}

// Get all cached poems from all chunks
export async function getAllCachedPoems(): Promise<PoemSummary[]> {
  const db = await getDB()
  const allChunks = await db.getAll('chunks')
  
  const allPoems: PoemSummary[] = []
  for (const chunk of allChunks) {
    if (chunk.poems && Array.isArray(chunk.poems)) {
      allPoems.push(...chunk.poems)
    }
  }
  
  return allPoems
}

// Cache authors data
export async function cacheAuthors(authors: AuthorStats[]) {
  const db = await getDB()
  await db.put('authors', {
    key: 'all',
    data: authors,
    timestamp: Date.now()
  })
}

// Get cached authors
export async function getCachedAuthors(): Promise<AuthorStats[] | null> {
  const db = await getDB()
  const cached = await db.get('authors', 'all')
  return cached?.data || null
}

// Clear authors cache
export async function clearAuthorsCache() {
  const db = await getDB()
  await db.delete('authors', 'all')
  // Also clear chunked cache
  await db.clear('authorChunks')
  await db.delete('authorMetadata', 'metadata')
}

// ==================== Author Chunks Cache (Incremental) ====================

// Cache a single author chunk
export async function cacheAuthorChunk(chunkId: number, authors: AuthorStats[]) {
  const db = await getDB()
  await db.put('authorChunks', {
    id: chunkId,
    authors,
    timestamp: Date.now()
  })
}

// Get a cached author chunk
export async function getCachedAuthorChunk(chunkId: number): Promise<AuthorStats[] | null> {
  const db = await getDB()
  const cached = await db.get('authorChunks', chunkId)
  return cached?.authors || null
}

// Update author metadata with loaded chunk IDs
export async function updateAuthorMetadata(chunkId: number, totalChunks: number) {
  const db = await getDB()
  const existing = await db.get('authorMetadata', 'metadata')
  const loadedChunkIds = existing ? [...existing.loadedChunkIds, chunkId] : [chunkId]
  await db.put('authorMetadata', {
    key: 'metadata',
    loadedChunkIds: [...new Set(loadedChunkIds)], // Remove duplicates
    totalChunks,
    timestamp: Date.now()
  })
}

// Get author metadata
export async function getAuthorMetadata(): Promise<{ loadedChunkIds: number[]; totalChunks: number } | null> {
  const db = await getDB()
  const cached = await db.get('authorMetadata', 'metadata')
  if (!cached) return null
  return {
    loadedChunkIds: cached.loadedChunkIds,
    totalChunks: cached.totalChunks
  }
}

// Get all cached author chunks merged
export async function getAllCachedAuthorChunks(): Promise<AuthorStats[] | null> {
  const db = await getDB()
  const metadata = await db.get('authorMetadata', 'metadata')
  if (!metadata || metadata.loadedChunkIds.length === 0) return null
  
  const allAuthors: AuthorStats[] = []
  for (const chunkId of metadata.loadedChunkIds) {
    const chunk = await db.get('authorChunks', chunkId)
    if (chunk) {
      allAuthors.push(...chunk.authors)
    }
  }
  return allAuthors.length > 0 ? allAuthors : null
}

// Check if all author chunks are cached
export async function areAllAuthorChunksCached(totalChunks: number): Promise<boolean> {
  const metadata = await getAuthorMetadata()
  if (!metadata) return false
  return metadata.loadedChunkIds.length >= totalChunks
}

// Get cached author chunk IDs
export async function getCachedAuthorChunkIds(): Promise<number[]> {
  const metadata = await getAuthorMetadata()
  return metadata?.loadedChunkIds || []
}

// ==================== Word Similarity Cache ====================

// Cache word similarity vocab
export async function cacheWordSimilarityVocab(vocab: Record<string, number>) {
  const db = await getDB()
  await db.put('wordSimilarityVocab', {
    key: 'vocab',
    data: vocab,
    timestamp: Date.now()
  })
}

// Get cached word similarity vocab
export async function getCachedWordSimilarityVocab(): Promise<Record<string, number> | null> {
  const db = await getDB()
  const cached = await db.get('wordSimilarityVocab', 'vocab')
  return cached?.data || null
}

// Cache word similarity chunk
export async function cacheWordSimilarityChunk(chunkId: number, chunk: WordSimilarityChunk) {
  const db = await getDB()
  // Convert Map to array for storage
  const entriesArray = Array.from(chunk.entries.entries())
  await db.put('wordSimilarityChunks', {
    id: chunkId,
    vocab: chunk.vocab,
    entries: entriesArray,
    timestamp: Date.now()
  })
}

// Get cached word similarity chunk
export async function getCachedWordSimilarityChunk(chunkId: number): Promise<WordSimilarityChunk | null> {
  const db = await getDB()
  const cached = await db.get('wordSimilarityChunks', chunkId)
  if (!cached) return null
  // Convert array back to Map
  return {
    vocab: cached.vocab,
    entries: new Map(cached.entries)
  }
}

// Get word similarity cache stats
export async function getWordSimilarityCacheStats(): Promise<{
  vocabCached: boolean
  chunks: number
  totalSize: number
}> {
  const db = await getDB()
  const vocab = await db.get('wordSimilarityVocab', 'vocab')
  const chunks = await db.getAll('wordSimilarityChunks')

  // Estimate size
  const vocabSize = vocab ? JSON.stringify(vocab).length * 2 : 0
  const chunksSize = chunks.reduce((sum, c) => {
    return sum + JSON.stringify(c).length * 2
  }, 0)

  return {
    vocabCached: !!vocab,
    chunks: chunks.length,
    totalSize: vocabSize + chunksSize
  }
}

// Get detailed word similarity cache info for dashboard
export async function getWordSimilarityCacheDetails(): Promise<{
  vocabCached: boolean
  vocabSize: number
  chunks: { id: number; entryCount: number; timestamp: number }[]
  totalSize: number
}> {
  const db = await getDB()
  const vocab = await db.get('wordSimilarityVocab', 'vocab')
  const allChunks = await db.getAll('wordSimilarityChunks')

  const vocabSize = vocab ? Object.keys(vocab.data).length : 0

  const chunks = allChunks.map(c => ({
    id: c.id,
    entryCount: c.entries.length,
    timestamp: c.timestamp
  }))

  // Estimate size
  const totalSize = allChunks.reduce((sum, c) => {
    return sum + JSON.stringify(c).length * 2
  }, 0) + (vocab ? JSON.stringify(vocab).length * 2 : 0)

  return {
    vocabCached: !!vocab,
    vocabSize,
    chunks,
    totalSize
  }
}

// Clear word similarity cache
export async function clearWordSimilarityCache() {
  const db = await getDB()
  await db.delete('wordSimilarityVocab', 'vocab')
  await db.clear('wordSimilarityChunks')
}
