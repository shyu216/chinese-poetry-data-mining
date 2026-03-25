/**
 * 文件: web/src/composables/useCacheV2.ts
 * 说明: 基于 IndexedDB（idb）的通用缓存层，封装键值缓存、分片缓存与元数据存储，用于跨模块持久化静态数据与分片状态。
 *
 * 数据管线:
 *   - 提供 `getCache` / `setCache` 用于普通键值缓存；`getChunkedCache` / `setChunkedCache` 用于按分片存储。
 *   - 提供 `metadata` 存储以记录已加载分片列表、版本与依赖哈希，用于缓存一致性检查。
 *
 * 性能与复杂度:
 *   - 单次读写为 O(1)（IndexedDB 单键访问）；清理某个 storage 下所有缓存为 O(m)，m = 该 storage 下的条目数（需遍历索引）。
 *   - 大批量读写时建议使用事务与批处理以减少 IO 开销。
 *
 * 注意事项:
 *   - IndexedDB 在不同浏览器/平台上的性能差异较大，批量写入应做性能测试与分片提交。
 *   - 元数据版本控制（`version` / `dependencyHash`）用于在数据结构变更时自动清理过期缓存。
 */
import { openDB, type DBSchema, type IDBPDatabase } from 'idb'

interface CacheItem<T = unknown> {
  key: string
  storage: string
  data: T
  timestamp: number
  expireAt?: number
  sourceUrl?: string
  hash?: string
  hashAlgorithm?: string
}

interface ChunkItem<T = unknown> {
  key: string
  storage: string
  chunkId: number | string
  data: T
  timestamp: number
  sourceUrl?: string
  hash?: string
  hashAlgorithm?: string
}

interface MetadataItem {
  storage: string
  loadedChunkIds: number[]
  totalChunks?: number
  timestamp: number
  /** 存储版本号，用于强制刷新缓存 */
  version?: number
  /** 依赖项哈希，用于验证依赖数据一致性 */
  dependencyHash?: string
  /** 存储特定的验证数据 */
  validationData?: Record<string, unknown>
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
  hash?: string
  hashAlgorithm?: string
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
    sourceUrl: options?.sourceUrl,
    hash: options?.hash,
    hashAlgorithm: options?.hashAlgorithm
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

// 带 hash 验证的缓存项结构（与 useVerifiedCache.ts 保持一致）
interface VerifiedCacheItem<T> {
  data: T
  fileHash: string
  manifestVersion: string
  cachedAt: number
}

/**
 * 获取带验证的分块缓存（支持 VerifiedCacheItem 包装结构）
 * 用于读取 useVerifiedCache 存储的数据
 */
export async function getVerifiedChunkedCache<T>(storage: string, chunkId: number | string): Promise<T | null> {
  const db = await getDB()
  const chunkKey = makeChunkKey(storage, chunkId)
  const item = await db.get('chunks', chunkKey)

  if (!item) return null

  const data = item.data as T | VerifiedCacheItem<T>

  // 检查是否是 VerifiedCacheItem 包装结构
  if (data && typeof data === 'object' && 'data' in data && 'fileHash' in data && 'cachedAt' in data) {
    return (data as VerifiedCacheItem<T>).data
  }

  // 普通数据结构，直接返回
  return data as T
}

export interface ChunkCacheOptions {
  sourceUrl?: string
  hash?: string
  hashAlgorithm?: string
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
    sourceUrl: options?.sourceUrl,
    hash: options?.hash,
    hashAlgorithm: options?.hashAlgorithm
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

/**
 * 存储验证配置
 */
export interface StorageValidationConfig {
  /** 存储名称 */
  storage: string
  /** 当前存储版本号 */
  currentVersion: number
  /** 依赖项验证函数，返回依赖项的哈希值 */
  getDependencyHash?: () => Promise<string | null>
  /** 依赖项数据获取函数 */
  getDependencyData?: () => Promise<Record<string, unknown> | null>
  /** 验证失败时的回调 */
  onValidationFailed?: (reason: string) => void
}

/**
 * 验证存储的缓存是否有效
 * 检查版本号和依赖项一致性
 */
export async function validateStorage(
  config: StorageValidationConfig
): Promise<{ valid: boolean; reason?: string; metadata?: MetadataItem | null }> {
  const meta = await getMetadata(config.storage)

  if (!meta) {
    return { valid: false, reason: '无元数据', metadata: null }
  }

  // 检查版本号
  if (meta.version !== config.currentVersion) {
    const reason = `版本不匹配: 缓存=${meta.version ?? '无'}, 当前=${config.currentVersion}`
    config.onValidationFailed?.(reason)
    return { valid: false, reason, metadata: meta }
  }

  // 检查依赖项哈希
  if (config.getDependencyHash) {
    const currentHash = await config.getDependencyHash()
    if (currentHash && meta.dependencyHash !== currentHash) {
      const reason = `依赖项哈希不匹配: 缓存=${meta.dependencyHash ?? '无'}, 当前=${currentHash}`
      config.onValidationFailed?.(reason)
      return { valid: false, reason, metadata: meta }
    }
  }

  // 检查依赖项数据
  if (config.getDependencyData) {
    const currentData = await config.getDependencyData()
    if (currentData && meta.validationData) {
      const cacheDataStr = JSON.stringify(meta.validationData)
      const currentDataStr = JSON.stringify(currentData)
      if (cacheDataStr !== currentDataStr) {
        const reason = '依赖项数据不匹配'
        config.onValidationFailed?.(reason)
        return { valid: false, reason, metadata: meta }
      }
    }
  }

  return { valid: true, metadata: meta }
}

/**
 * 验证并清理无效的存储缓存
 * 如果验证失败，自动清除该存储的所有缓存
 */
export async function validateAndCleanStorage(
  config: StorageValidationConfig & { autoClean?: boolean }
): Promise<{ valid: boolean; cleaned?: boolean; metadata?: MetadataItem | null }> {
  const result = await validateStorage(config)

  if (!result.valid && config.autoClean !== false) {
    console.warn(`[CacheV2] 存储 "${config.storage}" 验证失败: ${result.reason}，正在清除缓存...`)
    await clearStorage(config.storage)
    return { valid: false, cleaned: true, metadata: null }
  }

  return { valid: result.valid, cleaned: false, metadata: result.metadata }
}

/**
 * 获取带验证的元数据
 * 如果验证失败，返回 null
 */
export async function getValidatedMetadata(
  storage: string,
  currentVersion: number,
  options?: {
    getDependencyHash?: () => Promise<string | null>
    autoClean?: boolean
  }
): Promise<MetadataItem | null> {
  const result = await validateAndCleanStorage({
    storage,
    currentVersion,
    getDependencyHash: options?.getDependencyHash,
    autoClean: options?.autoClean
  })

  return result.valid ? result.metadata ?? null : null
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

  // 使用 getAll 替代 cursor 遍历，性能更好
  const allChunks = await db.getAllFromIndex('chunks', 'by-storage', storage)
  const chunks: StorageStats['chunks'] = allChunks.map(item => ({
    chunkId: item.chunkId,
    size: estimateSize(item.data),
    timestamp: item.timestamp,
    sourceUrl: item.sourceUrl
  }))
  const chunkTotalSize = chunks.reduce((sum, c) => sum + c.size, 0)

  const allCaches = await db.getAllFromIndex('cache', 'by-storage', storage)
  const caches: StorageStats['caches'] = allCaches.map(item => ({
    key: item.key.replace(`${storage}:`, ''),
    size: estimateSize(item.data),
    timestamp: item.timestamp,
    sourceUrl: item.sourceUrl
  }))
  const cacheTotalSize = caches.reduce((sum, c) => sum + c.size, 0)

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
