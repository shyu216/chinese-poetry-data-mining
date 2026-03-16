# IndexedDB 统一缓存系统设计

**日期**: 2026-03-16
**目标**: 分析现有 IndexedDB 使用情况，设计统一的缓存系统

---

## 1. 现状分析

### 1.1 使用 IndexedDB 的模块

| 模块 | 缓存内容 | 存储类型 |
|------|---------|---------|
| `usePoems.ts` | 诗词摘要、分块详情、索引、元数据 | 分块存储 |
| `useAuthors.ts` | 作者统计数据 | 分块增量存储 |
| `useWordSimilarity.ts` | 词表、相似词分块 | 分块存储 |

### 1.2 不使用 IndexedDB 的模块

| 模块 | 当前缓存方式 | 问题 |
|------|-------------|------|
| `useSearchIndex.ts` | 仅内存缓存 (poemChunkCache, keywordCache) | 刷新页面后数据丢失 |

### 1.3 现有 Schema (usePoemCache.ts)

```typescript
// 现有存储对象
- chunks: 诗词摘要分块
- chunkDetails: 诗词详情分块
- index: 索引数据
- metadata: 已加载分块ID
- authors: 全部作者数据
- authorChunks: 作者分块
- authorMetadata: 作者加载元数据
- wordSimilarityVocab: 词相似度词表
- wordSimilarityChunks: 词相似度分块
```

---

## 2. 问题分析

### 2.1 主要问题

1. **缓存策略不统一**: 不同模块各自实现缓存逻辑
2. **useSearchIndex 缺失**: 完全没有使用 IndexedDB
3. **Schema 分散**: 每个功能模块有独立的 Object Store
4. **缺乏通用 API**: 无法方便地复用缓存逻辑

### 2.2 代码重复

- `loadChunk` 模式在多个地方重复
- 缓存检查逻辑重复
- 没有统一的错误处理

---

## 3. 统一缓存系统设计

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                     useCache.ts                          │
│              (统一的缓存服务层)                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  CacheCore  │  │  StorageMgr  │  │  SchemaMgr  │     │
│  │  (核心API)  │  │  (存储管理)  │  │  (版本管理)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                     IndexedDB                            │
└─────────────────────────────────────────────────────────┘
           ▲                    ▲                    ▲
           │                    │                    │
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  usePoems    │    │  useAuthors  │    │useSearchIndex│
    │  (已有)      │    │  (已有)      │    │  (需改造)    │
    └──────────────┘    └──────────────┘    └──────────────┘
```

### 3.2 核心 API 设计

```typescript
// useCache.ts - 统一的缓存服务

interface CacheOptions {
  expire?: number      // 过期时间 (ms)
  storage?: string     // 存储区域
}

interface CacheStats {
  keys: number
  size: number
  lastUpdate: number
}

// 基础缓存操作
function getCache<T>(key: string, options?: CacheOptions): Promise<T | null>
function setCache<T>(key: string, value: T, options?: CacheOptions): Promise<void>
function deleteCache(key: string): Promise<boolean>
function clearCache(storage?: string): Promise<void>
function getCacheStats(storage?: string): Promise<CacheStats>

// 批量操作
function getManyCache<T>(keys: string[]): Promise<Map<string, T | null>>
function setManyCache<T>(entries: [string, T][], options?: CacheOptions): Promise<void>

// 分块缓存 (用于大数据)
function getChunkedCache<T>(storage: string, chunkId: number): Promise<T | null>
function setChunkedCache<T>(storage: string, chunkId: number, data: T): Promise<void>
function hasChunk(storage: string, chunkId: number): Promise<boolean>
function getAllChunkIds(storage: string): Promise<number[]>
function getAllChunkedData<T>(storage: string): Promise<T[]>

// 元数据管理
function setMetadata(storage: string, meta: Record<string, any>): Promise<void>
function getMetadata(storage: string): Promise<Record<string, any> | null>
```

### 3.3 Schema 设计

```typescript
// 统一 Schema

interface UnifiedCacheSchema extends DBSchema {
  // 通用缓存存储
  cache: {
    key: string
    value: {
      key: string
      storage: string
      data: any
      timestamp: number
      expireAt?: number
    }
    indexes: { 'by-storage': string }
  }
  
  // 分块数据存储
  chunks: {
    key: string  // "storage:chunkId"
    value: {
      storage: string
      chunkId: number
      data: any
      timestamp: number
    }
    indexes: { 'by-storage': string }
  }
  
  // 元数据存储
  metadata: {
    key: string  // storage name
    value: {
      storage: string
      loadedChunkIds: number[]
      totalChunks?: number
      timestamp: number
    }
  }
  
  // 存储统计
  stats: {
    key: string
    value: {
      storage: string
      key: string
      size: number
      lastUpdate: number
    }
  }
}
```

---

## 4. 实际实施

> **架构决策**: 考虑到现有模块 (usePoems, useAuthors, useWordSimilarity) 已稳定运行，采用渐进式方案：
> - 新模块直接使用 `useCache.ts`
> - 现有模块保持不变，未来按需迁移

### 4.1 第一阶段：创建统一缓存服务 ✅ 已完成

**目标**: 创建 `useCache.ts`，提供通用缓存能力

**任务**:
1. 创建 `web/src/composables/useCache.ts`
2. 实现基础缓存 API
3. 实现分块缓存 API
4. 添加存储空间管理

### 4.2 第二阶段：改造 useSearchIndex ✅ 已完成

**目标**: 为搜索索引添加 IndexedDB 缓存

**已完成**:
- 创建 `useCache.ts` 统一缓存服务
- 改造 `useSearchIndex.ts`:
  - 添加 `initialize()` 方法从 IndexedDB 恢复状态
  - Manifest 自动缓存和恢复
  - 诗歌分块增量缓存
- 新增导出: `error`, `initialize`, `loadedChunkIds`

### 4.3 第三阶段：重构现有模块 - 延后

**状态**: 延后实施

原因：现有模块 (usePoems, useAuthors, useWordSimilarity) 已稳定运行，改动风险高。

**未来可按需迁移**:
- 新功能直接使用 `useCache.ts`
- 旧模块逐步迁移

---

## 5. API 使用示例

### 5.1 基础缓存

```typescript
import { getCache, setCache, deleteCache } from './useCache'

// 缓存简单数据
await setCache('user-preferences', { theme: 'dark' })
const prefs = await getCache('user-preferences')

// 带过期时间
await setCache('api-response', data, { expire: 3600000 })
```

### 5.2 分块缓存

```typescript
import { 
  getChunkedCache, 
  setChunkedCache, 
  getAllChunkedData,
  setMetadata 
} from './useCache'

// 缓存诗词分块
await setChunkedCache('poems', chunkId, poems)
const poems = await getChunkedCache('poems', chunkId)

// 缓存元数据
await setMetadata('poems', { 
  loadedChunkIds: [1, 2, 3], 
  totalChunks: 100 
})

// 获取所有已缓存的分块
const allPoems = await getAllChunkedData('poems')
```

### 5.3 useSearchIndex 改造示例

```typescript
// 改造后的 useSearchIndex.ts
import { 
  getChunkedCache, 
  setChunkedCache, 
  getCache, 
  setCache,
  getMetadata
} from './useCache'

export function useSearchIndex() {
  // 加载 manifest - 使用缓存
  const loadManifest = async (): Promise<Manifest | null> => {
    // 先检查缓存
    const cached = await getCache<Manifest>('search:manifest')
    if (cached) return cached
    
    // 加载并缓存
    const data = await fetchManifest()
    await setCache('search:manifest', data)
    return data
  }

  // 加载诗歌分块 - 使用分块缓存
  const loadPoemChunk = async (prefix: string): Promise<Map<string, PoemSummary> | null> => {
    // 先检查分块缓存
    const chunkId = parseInt(prefix)
    const cached = await getChunkedCache<Map<string, PoemSummary>>('poem-chunks', chunkId)
    if (cached) return cached
    
    // 加载并缓存
    const data = await fetchPoemChunk(prefix)
    await setChunkedCache('poem-chunks', chunkId, data)
    return data
  }

  // 初始化时恢复缓存状态
  const initialize = async () => {
    const meta = await getMetadata('poem-chunks')
    if (meta) {
      // 恢复已加载的分块信息
      loadedChunkIds.value = meta.loadedChunkIds
    }
  }
}
```

---

## 6. 缓存失效策略

### 6.1 过期策略

```typescript
// 自动清理过期数据
async function cleanupExpired(): Promise<number> {
  const db = await getDB()
  const tx = db.transaction('cache', 'readwrite')
  const store = tx.objectStore('cache')
  const now = Date.now()
  
  let deleted = 0
  let cursor = await store.openCursor()
  
  while (cursor) {
    if (cursor.value.expireAt && cursor.value.expireAt < now) {
      await cursor.delete()
      deleted++
    }
    cursor = await cursor.continue()
  }
  
  return deleted
}
```

### 6.2 存储配额管理

```typescript
// 检查存储空间
async function checkStorageQuota(): Promise<{ used: number; quota: number }> {
  if (navigator.storage && navigator.storage.estimate) {
    const estimate = await navigator.storage.estimate()
    return {
      used: estimate.usage || 0,
      quota: estimate.quota || 0
    }
  }
  return { used: 0, quota: 0 }
}

// 空间不足时清理
async function evictOldest(storage: string, targetFree: number): Promise<void> {
  const stats = await getStorageStats(storage)
  // 按时间排序，删除最旧的数据
  // ...
}
```

---

## 7. 迁移检查清单

- [x] 创建 `useCache.ts` 统一缓存服务
- [x] 改造 `useSearchIndex.ts` 使用 IndexedDB
- [ ] 添加缓存统计 API (使用 useCache 已有)
- [ ] 添加缓存清理/失效机制 (使用 useCache 已有)
- [ ] 更新文档

---

## 8. 相关文件位置

- 现有缓存: `web/src/composables/usePoemCache.ts`
- **新增缓存**: `web/src/composables/useCache.ts`
- 已改造: `web/src/composables/useSearchIndex.ts`
