/**
 * @overview
 * file: web/src/search/LRUCache.ts
 * category: utility / cache
 * tech: TypeScript
 * summary: 简单的内存 LRU 缓存实现，支持最大容量与可选 TTL，用于缓存搜索结果与中间计算结果。
 *
 * Data pipeline (conceptual):
 *  - put/get 操作维护 Map 中的条目与访问时间
 *  - 当容量超过限制时，基于最近最少使用（LRU）策略淘汰最旧条目
 *
 * Complexity & notes:
 *  - get/set 的查找为 O(1)（基于 Map），但当前实现的淘汰算法为 O(n)（扫描寻找最旧），适用于中小容量
 *  - 若需要在高并发或大容量场景中使用，建议改用双向链表 + 哈希表实现以实现 O(1) 淘汰
 *
 * Potential issues & recommendations:
 *  - 当前实现的 evictLRU 在缓存很大时为 O(n)，可替换为更高效的数据结构
 *  - 为持久化缓存或跨会话缓存，可结合 IndexedDB，但需处理序列化与 TTL
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
