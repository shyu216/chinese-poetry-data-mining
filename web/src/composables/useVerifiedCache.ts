/**
 * 带 Hash 验证的缓存组合式函数
 * 用于静态数据文件的版本控制和缓存验证
 */

import { ref, computed } from 'vue'
import { getCache, setCache, getChunkedCache, setChunkedCache, type CacheOptions, type ChunkCacheOptions } from './useCacheV2'

// Hash Manifest 类型
interface HashManifest {
  version: string
  generatedAt: number
  files: Record<string, string>
}

// 带 hash 的缓存项
interface VerifiedCacheItem<T> {
  data: T
  fileHash: string
  manifestVersion: string
  cachedAt: number
}

// 验证结果
interface VerificationResult<T> {
  data: T | null
  valid: boolean
  fromCache: boolean
  hashMatch: boolean
  error?: string
}

// 全局 manifest 缓存
let manifestPromise: Promise<HashManifest> | null = null

/**
 * 获取 hash manifest
 */
async function getManifest(): Promise<HashManifest> {
  if (!manifestPromise) {
    manifestPromise = fetch(`${import.meta.env.BASE_URL}/data/hash-manifest.json`)
      .then(res => {
        if (!res.ok) throw new Error('Manifest not found')
        return res.json()
      })
      .catch(err => {
        console.warn('[VerifiedCache] Manifest fetch failed:', err)
        // 返回空 manifest，允许降级到无验证模式
        return { version: '', generatedAt: 0, files: {} }
      })
  }
  return manifestPromise
}

/**
 * 清除 manifest 缓存（用于热更新场景）
 */
export function clearManifestCache(): void {
  manifestPromise = null
}

/**
 * 获取文件的当前 hash
 */
export async function getFileHash(filePath: string): Promise<string | null> {
  const manifest = await getManifest()
  return manifest.files[filePath] || null
}

/**
 * 检查文件是否有更新
 */
export async function isFileUpdated(filePath: string, cachedHash: string): Promise<boolean> {
  const currentHash = await getFileHash(filePath)
  if (!currentHash) return false // manifest 不可用，假设未更新
  return currentHash !== cachedHash
}

/**
 * 带验证的缓存获取
 */
export async function getVerifiedCache<T>(
  storage: string,
  key: string,
  filePath: string,
  loader: () => Promise<T>
): Promise<VerificationResult<T>> {
  try {
    // 1. 获取当前文件的 hash
    const currentHash = await getFileHash(filePath)

    // 2. 尝试读取缓存
    const cached = await getCache<VerifiedCacheItem<T>>(storage, key)

    // 3. 如果 manifest 不可用，直接返回缓存数据（降级）
    if (!currentHash) {
      if (cached) {
        return {
          data: cached.data,
          valid: true,
          fromCache: true,
          hashMatch: false
        }
      }
      // 没有缓存，加载数据但不存储 hash
      const data = await loader()
      await setCache(storage, key, { data, fileHash: '', manifestVersion: '', cachedAt: Date.now() })
      return {
        data,
        valid: true,
        fromCache: false,
        hashMatch: false
      }
    }

    // 4. 检查缓存是否有效（hash 匹配）
    if (cached && cached.fileHash === currentHash) {
      console.log(`[VerifiedCache] Hit: ${filePath}`)
      return {
        data: cached.data,
        valid: true,
        fromCache: true,
        hashMatch: true
      }
    }

    // 5. 缓存缺失或过期，重新加载
    console.log(`[VerifiedCache] Miss: ${filePath}, loading...`)
    const data = await loader()

    // 6. 存储到缓存
    const manifest = await getManifest()
    await setCache(storage, key, {
      data,
      fileHash: currentHash,
      manifestVersion: manifest.version,
      cachedAt: Date.now()
    }, {
      hash: currentHash,
      hashAlgorithm: 'sha256'
    })

    return {
      data,
      valid: true,
      fromCache: false,
      hashMatch: true
    }
  } catch (error) {
    console.error(`[VerifiedCache] Error loading ${filePath}:`, error)
    return {
      data: null,
      valid: false,
      fromCache: false,
      hashMatch: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

/**
 * 带验证的分块缓存获取
 */
export async function getVerifiedChunk<T>(
  storage: string,
  chunkId: number | string,
  filePath: string,
  loader: () => Promise<T>
): Promise<VerificationResult<T>> {
  console.log(`[VerifiedCache] getVerifiedChunk START: ${filePath}`)
  try {
    const hashStart = Date.now()
    const currentHash = await getFileHash(filePath)
    console.log(`[VerifiedCache] got file hash in ${Date.now() - hashStart}ms: ${currentHash ? currentHash.slice(0, 8) + '...' : 'null'}`)

    const cacheStart = Date.now()
    const cached = await getChunkedCache<VerifiedCacheItem<T>>(storage, chunkId)
    console.log(`[VerifiedCache] got chunked cache in ${Date.now() - cacheStart}ms: ${cached ? 'hit' : 'miss'}`)

    if (!currentHash) {
      console.log(`[VerifiedCache] no current hash, using cache or loader`)
      if (cached) {
        return {
          data: cached.data,
          valid: true,
          fromCache: true,
          hashMatch: false
        }
      }
      const data = await loader()
      await setChunkedCache(storage, chunkId, { data, fileHash: '', manifestVersion: '', cachedAt: Date.now() })
      return {
        data,
        valid: true,
        fromCache: false,
        hashMatch: false
      }
    }

    if (cached && cached.fileHash === currentHash) {
      console.log(`[VerifiedCache] Chunk Hit: ${filePath}`)
      return {
        data: cached.data,
        valid: true,
        fromCache: true,
        hashMatch: true
      }
    }

    console.log(`[VerifiedCache] Chunk Miss: ${filePath}, loading...`)
    const loaderStart = Date.now()
    const data = await loader()
    console.log(`[VerifiedCache] loader completed in ${Date.now() - loaderStart}ms`)
    const manifest = await getManifest()

    await setChunkedCache(storage, chunkId, {
      data,
      fileHash: currentHash,
      manifestVersion: manifest.version,
      cachedAt: Date.now()
    }, {
      hash: currentHash,
      hashAlgorithm: 'sha256'
    })

    return {
      data,
      valid: true,
      fromCache: false,
      hashMatch: true
    }
  } catch (error) {
    console.error(`[VerifiedCache] Error loading chunk ${filePath}:`, error)
    return {
      data: null,
      valid: false,
      fromCache: false,
      hashMatch: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

/**
 * 批量预加载多个文件
 */
export async function preloadVerifiedFiles<T>(
  storage: string,
  files: Array<{ key: string; filePath: string; loader: () => Promise<T> }>
): Promise<Map<string, VerificationResult<T>>> {
  const results = new Map<string, VerificationResult<T>>()

  await Promise.all(
    files.map(async ({ key, filePath, loader }) => {
      const result = await getVerifiedCache(storage, key, filePath, loader)
      results.set(key, result)
    })
  )

  return results
}

/**
 * Vue 组合式函数：使用带验证的缓存
 */
export function useVerifiedCache() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const stats = ref({
    cacheHits: 0,
    cacheMisses: 0,
    hashMismatches: 0
  })

  const isReady = computed(() => !loading.value && !error.value)

  /**
   * 加载数据（带验证）
   */
  async function load<T>(
    storage: string,
    key: string,
    filePath: string,
    loader: () => Promise<T>
  ): Promise<T | null> {
    loading.value = true
    error.value = null

    try {
      const result = await getVerifiedCache(storage, key, filePath, loader)

      if (result.fromCache) {
        stats.value.cacheHits++
      } else {
        stats.value.cacheMisses++
      }

      if (!result.hashMatch && result.fromCache) {
        stats.value.hashMismatches++
      }

      if (result.error) {
        error.value = result.error
      }

      return result.data
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载分块数据
   */
  async function loadChunk<T>(
    storage: string,
    chunkId: number | string,
    filePath: string,
    loader: () => Promise<T>
  ): Promise<T | null> {
    loading.value = true
    error.value = null

    try {
      const result = await getVerifiedChunk(storage, chunkId, filePath, loader)

      if (result.fromCache) {
        stats.value.cacheHits++
      } else {
        stats.value.cacheMisses++
      }

      if (result.error) {
        error.value = result.error
      }

      return result.data
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置统计
   */
  function resetStats() {
    stats.value = {
      cacheHits: 0,
      cacheMisses: 0,
      hashMismatches: 0
    }
  }

  return {
    loading,
    error,
    isReady,
    stats,
    load,
    loadChunk,
    resetStats,
    clearManifestCache
  }
}
