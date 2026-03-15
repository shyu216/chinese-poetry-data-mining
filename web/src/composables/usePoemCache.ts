import { openDB, type DBSchema, type IDBPDatabase } from 'idb'
import type { PoemSummary, PoemDetail } from './usePoems'
import type { AuthorStats } from '@/types/author'

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
      data: any
      timestamp: number
    }
  }
  metadata: {
    key: string
    value: {
      loadedChunkIds: number[]
      timestamp: number
    }
  }
  authors: {
    key: string
    value: {
      data: AuthorStats[]
      timestamp: number
    }
  }
}

const DB_NAME = 'poem-cache'
const DB_VERSION = 2

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
}
