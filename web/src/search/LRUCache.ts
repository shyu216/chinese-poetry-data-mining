/**
 * LRU 内存缓存
 * 用于缓存搜索结果和频繁访问的数据
 */

interface CacheEntry<T> {
  value: T
  lastAccessed: number
  accessCount: number
}

export class LRUCache<T> {
  private cache = new Map<string, CacheEntry<T>>()
  private maxSize: number
  private defaultTTL?: number

  constructor(maxSize: number, defaultTTL?: number) {
    this.maxSize = maxSize
    this.defaultTTL = defaultTTL
  }

  get(key: string): T | undefined {
    const entry = this.cache.get(key)
    if (!entry) return undefined

    // 检查是否过期
    if (this.defaultTTL && Date.now() - entry.lastAccessed > this.defaultTTL) {
      this.cache.delete(key)
      return undefined
    }

    // 更新访问信息
    entry.lastAccessed = Date.now()
    entry.accessCount++

    return entry.value
  }

  set(key: string, value: T): void {
    // 如果已存在，更新值
    if (this.cache.has(key)) {
      this.cache.set(key, {
        value,
        lastAccessed: Date.now(),
        accessCount: this.cache.get(key)!.accessCount + 1
      })
      return
    }

    // 如果超出容量，淘汰最久未使用的
    if (this.cache.size >= this.maxSize) {
      this.evictLRU()
    }

    this.cache.set(key, {
      value,
      lastAccessed: Date.now(),
      accessCount: 1
    })
  }

  private evictLRU(): void {
    let oldestKey: string | null = null
    let oldestTime = Infinity

    for (const [key, entry] of this.cache) {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed
        oldestKey = key
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey)
    }
  }

  clear(): void {
    this.cache.clear()
  }

  size(): number {
    return this.cache.size
  }

  keys(): string[] {
    return Array.from(this.cache.keys())
  }
}
