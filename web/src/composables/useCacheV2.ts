import { openDB, type DBSchema, type IDBPDatabase } from 'idb'

interface CacheItem<T = unknown> {
  key: string
  storage: string
  data: T
  timestamp: number
  expireAt?: number
  sourceUrl?: string
}

interface ChunkItem<T = unknown> {
  key: string
  storage: string
  chunkId: number | string
  data: T
  timestamp: number
  sourceUrl?: string
}

interface MetadataItem {
  storage: string
  loadedChunkIds: number[]
  totalChunks?: number
  timestamp: number
}

interface UnifiedCacheSchema extends DBSchema {
  cache: {
    key: string
    value: CacheItem
    indexes: { 'by-storage': string }
  }
  chunks: {
    key: string
    value: ChunkItem
    indexes: { 'by-storage': string }
  }
  metadata: {
    key: string
    value: MetadataItem
  }
}

const DB_NAME = 'cache-v2'
const DB_VERSION = 1

let dbPromise: Promise<IDBPDatabase<UnifiedCacheSchema>> | null = null

export function getDB() {
  if (!dbPromise) {
    dbPromise = openDB<UnifiedCacheSchema>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('cache')) {
          const cacheStore = db.createObjectStore('cache', { keyPath: 'key' })
          cacheStore.createIndex('by-storage', 'storage')
        }
        if (!db.objectStoreNames.contains('chunks')) {
          const chunkStore = db.createObjectStore('chunks', { keyPath: 'key' })
          chunkStore.createIndex('by-storage', 'storage')
        }
        if (!db.objectStoreNames.contains('metadata')) {
          db.createObjectStore('metadata', { keyPath: 'storage' })
        }
      }
    })
  }
  return dbPromise
}

function makeCacheKey(storage: string, key: string): string {
  return `${storage}:${key}`
}

function makeChunkKey(storage: string, chunkId: number | string): string {
  return `${storage}:chunk:${chunkId}`
}

export interface CacheOptions {
  expire?: number
  storage?: string
  sourceUrl?: string
}

export async function getCache<T>(storage: string, key: string): Promise<T | null> {
  const db = await getDB()
  const cacheKey = makeCacheKey(storage, key)
  const item = await db.get('cache', cacheKey)

  if (!item) return null

  if (item.expireAt && item.expireAt < Date.now()) {
    await db.delete('cache', cacheKey)
    return null
  }

  return item.data as T
}

export async function setCache<T>(storage: string, key: string, data: T, options?: CacheOptions): Promise<void> {
  const db = await getDB()
  const cacheKey = makeCacheKey(storage, key)

  await db.put('cache', {
    key: cacheKey,
    storage,
    data,
    timestamp: Date.now(),
    expireAt: options?.expire ? Date.now() + options.expire : undefined,
    sourceUrl: options?.sourceUrl
  })
}

export async function deleteCache(storage: string, key: string): Promise<boolean> {
  const db = await getDB()
  const cacheKey = makeCacheKey(storage, key)
  const existed = await db.getKey('cache', cacheKey)
  if (existed) {
    await db.delete('cache', cacheKey)
    return true
  }
  return false
}

export async function clearCache(storage?: string): Promise<void> {
  const db = await getDB()

  if (storage) {
    const tx = db.transaction('cache', 'readwrite')
    const index = tx.store.index('by-storage')
    let cursor = await index.openCursor(IDBKeyRange.only(storage))

    while (cursor) {
      await cursor.delete()
      cursor = await cursor.continue()
    }

    await tx.done
  } else {
    await db.clear('cache')
  }
}

export async function getChunkedCache<T>(storage: string, chunkId: number | string): Promise<T | null> {
  const db = await getDB()
  const chunkKey = makeChunkKey(storage, chunkId)
  const item = await db.get('chunks', chunkKey)

  if (!item) return null

  return item.data as T
}

export interface ChunkCacheOptions {
  sourceUrl?: string
}

export async function setChunkedCache<T>(storage: string, chunkId: number | string, data: T, options?: ChunkCacheOptions): Promise<void> {
  const db = await getDB()
  const chunkKey = makeChunkKey(storage, chunkId)

  await db.put('chunks', {
    key: chunkKey,
    storage,
    chunkId,
    data,
    timestamp: Date.now(),
    sourceUrl: options?.sourceUrl
  })
}

export async function getMetadata(storage: string): Promise<MetadataItem | null> {
  const db = await getDB()
  const result = await db.get('metadata', storage)
  return result ?? null
}

export async function setMetadata(storage: string, data: Omit<MetadataItem, 'storage' | 'timestamp'>): Promise<void> {
  const db = await getDB()
  await db.put('metadata', {
    storage,
    ...data,
    timestamp: Date.now()
  })
}

export async function getAllChunkIds(storage: string): Promise<number[]> {
  const meta = await getMetadata(storage)
  return meta?.loadedChunkIds || []
}

export async function clearStorage(storage: string): Promise<void> {
  const db = await getDB()

  await db.delete('cache', makeCacheKey(storage, '*'))

  const tx = db.transaction('chunks', 'readwrite')
  const index = tx.store.index('by-storage')
  let cursor = await index.openCursor(IDBKeyRange.only(storage))

  while (cursor) {
    await cursor.delete()
    cursor = await cursor.continue()
  }

  await tx.done
  await db.delete('metadata', storage)
}

export interface StorageStats {
  storage: string
  chunkCount: number
  cacheCount: number
  totalSize: number
  chunks: Array<{
    chunkId: number | string
    size: number
    timestamp: number
    sourceUrl?: string
  }>
  caches: Array<{
    key: string
    size: number
    timestamp: number
    sourceUrl?: string
  }>
}

export interface BrowserStorageInfo {
  indexedDB: {
    name: string
    version: number
    objectStores: string[]
    estimatedSize: number
  }
  localStorage: {
    itemCount: number
    estimatedSize: number
    items: Array<{ key: string; size: number }>
  }
  sessionStorage: {
    itemCount: number
    estimatedSize: number
    items: Array<{ key: string; size: number }>
  }
  cookies: Array<{ name: string; domain: string; size: number }>
  quota: {
    usage: number
    quota: number
    usageDetails?: Record<string, number>
  } | null
}

function estimateSize(data: unknown): number {
  try {
    return new Blob([JSON.stringify(data)]).size
  } catch {
    return 0
  }
}

export async function getStorageStats(storage: string): Promise<StorageStats> {
  const db = await getDB()

  const chunks: StorageStats['chunks'] = []
  let chunkTotalSize = 0

  const tx = db.transaction('chunks', 'readonly')
  const index = tx.store.index('by-storage')
  let cursor = await index.openCursor(IDBKeyRange.only(storage))

  while (cursor) {
    const item = cursor.value
    const size = estimateSize(item.data)
    chunks.push({
      chunkId: item.chunkId,
      size,
      timestamp: item.timestamp,
      sourceUrl: item.sourceUrl
    })
    chunkTotalSize += size
    cursor = await cursor.continue()
  }

  await tx.done

  const caches: StorageStats['caches'] = []
  let cacheTotalSize = 0

  const cacheTx = db.transaction('cache', 'readonly')
  const cacheIndex = cacheTx.store.index('by-storage')
  let cacheCursor = await cacheIndex.openCursor(IDBKeyRange.only(storage))

  while (cacheCursor) {
    const item = cacheCursor.value
    const size = estimateSize(item.data)
    caches.push({
      key: item.key.replace(`${storage}:`, ''),
      size,
      timestamp: item.timestamp,
      sourceUrl: item.sourceUrl
    })
    cacheTotalSize += size
    cacheCursor = await cacheCursor.continue()
  }

  await cacheTx.done

  return {
    storage,
    chunkCount: chunks.length,
    cacheCount: caches.length,
    totalSize: chunkTotalSize + cacheTotalSize,
    chunks,
    caches
  }
}

export async function getAllStorageStats(): Promise<StorageStats[]> {
  const db = await getDB()
  const metadata = await db.getAll('metadata')
  const storages = metadata.map(m => m.storage)

  const stats = await Promise.all(storages.map(s => getStorageStats(s)))
  return stats
}

export async function getBrowserStorageInfo(): Promise<BrowserStorageInfo> {
  const db = await getDB()
  const dbInfo = await db.getAll('metadata')

  const idbInfo: BrowserStorageInfo['indexedDB'] = {
    name: 'cache-v2',
    version: 1,
    objectStores: ['cache', 'chunks', 'metadata'],
    estimatedSize: 0
  }

  for (const meta of dbInfo) {
    const stats = await getStorageStats(meta.storage)
    idbInfo.estimatedSize += stats.totalSize
  }

  const localStorageItems: BrowserStorageInfo['localStorage']['items'] = []
  let localStorageSize = 0
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key) {
      const value = localStorage.getItem(key) || ''
      const size = new Blob([value]).size
      localStorageItems.push({ key, size })
      localStorageSize += size
    }
  }

  const sessionStorageItems: BrowserStorageInfo['sessionStorage']['items'] = []
  let sessionStorageSize = 0
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i)
    if (key) {
      const value = sessionStorage.getItem(key) || ''
      const size = new Blob([value]).size
      sessionStorageItems.push({ key, size })
      sessionStorageSize += size
    }
  }

  const cookies: BrowserStorageInfo['cookies'] = []
  const cookieStr = document.cookie
  if (cookieStr) {
    cookieStr.split(';').forEach(cookie => {
      const [nameValue] = cookie.trim().split(';')
      const [name = ''] = (nameValue || '').split('=')
      cookies.push({
        name: name.trim(),
        domain: window.location.hostname,
        size: new Blob([cookie.trim()]).size
      })
    })
  }

  let quota: BrowserStorageInfo['quota'] = null
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    try {
      const estimate = await navigator.storage.estimate()
      quota = {
        usage: estimate.usage || 0,
        quota: estimate.quota || 0,
        usageDetails: (estimate as StorageEstimate & { usageDetails?: Record<string, number> }).usageDetails
      }
    } catch {
      // ignore
    }
  }

  return {
    indexedDB: idbInfo,
    localStorage: {
      itemCount: localStorageItems.length,
      estimatedSize: localStorageSize,
      items: localStorageItems
    },
    sessionStorage: {
      itemCount: sessionStorageItems.length,
      estimatedSize: sessionStorageSize,
      items: sessionStorageItems
    },
    cookies,
    quota
  }
}
