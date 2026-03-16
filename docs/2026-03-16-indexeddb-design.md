# IndexedDB 统一缓存系统设计

**日期**: 2026-03-16
**版本**: v2.0
**状态**: 已实施
**目标**: 分析现有 IndexedDB 使用情况，设计并实现统一的缓存系统

---

## 📋 目录

1. [执行摘要](#1-执行摘要)
2. [现状分析](#2-现状分析)
3. [问题分析](#3-问题分析)
4. [架构设计](#4-架构设计)
5. [详细设计](#5-详细设计)
6. [实施记录](#6-实施记录)
7. [API 参考](#7-api-参考)
8. [缓存策略](#8-缓存策略)
9. [测试策略](#9-测试策略)
10. [版本迁移](#10-版本迁移)
11. [检查清单](#11-检查清单)

---

## 1. 执行摘要

### 1.1 项目背景

中国古典诗词数据挖掘项目包含多个数据模块：诗词、诗人、字词统计、搜索索引、词语相似度等。每个模块独立实现数据加载和缓存逻辑，导致：

- **代码重复**: `loadChunk` 模式在多处重复实现
- **维护困难**: 缓存逻辑分散，难以统一优化
- **体验不一致**: 部分模块刷新后数据丢失（如 useSearchIndex）

### 1.2 解决方案

设计并实现统一的 IndexedDB 缓存系统，提供：

- 通用的缓存 API
- 分块数据管理
- 元数据追踪
- 过期机制
- 存储配额管理

### 1.3 实施成果

| 阶段 | 状态 | 说明 |
|------|------|------|
| 统一缓存服务 | ✅ 完成 | `useCacheV2.ts` |
| 搜索索引改造 | ✅ 完成 | 使用 IndexedDB |
| composables_v2 | ✅ 完成 | 全新框架 |

---

## 2. 现状分析

### 2.1 数据模块总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           数据模块架构                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │   usePoems   │  │  useAuthors  │  │useWordSimilarity│             │
│  │  (诗词数据)   │  │   (诗人数据)  │  │  (词语相似度)  │                │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │
│         │                  │                  │                         │
│         ▼                  ▼                  ▼                         │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │                    IndexedDB                              │          │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │          │
│  │  │   poems    │ │  authors   │ │ wordSimilarity     │   │          │
│  │  │  chunks    │ │  chunks    │ │ chunks             │   │          │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐                                   │
│  │ useSearchIndex│  │ useWordcount │                                   │
│  │  (搜索索引)   │  │  (字词统计)  │                                   │
│  └──────┬───────┘  └──────┬───────┘                                   │
│         │                  │                                            │
│         ▼                  ▼                                            │
│  ┌──────────────────────────────────────────────────────┐               │
│  │                    ❌ 无缓存                          │               │
│  │         (刷新页面后数据丢失)                          │               │
│  └──────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 现有 IndexedDB Schema

| Object Store | 用途 | 存储内容 |
|--------------|------|----------|
| `chunks` | 诗词摘要分块 | `{ id, poems, timestamp }` |
| `chunkDetails` | 诗词详情分块 | `{ id, poems, timestamp }` |
| `index` | 索引数据 | 搜索索引元数据 |
| `metadata` | 已加载分块ID | `{ key, loadedChunkIds }` |
| `authors` | 全部作者数据 | 作者统计数据 |
| `authorChunks` | 作者分块 | `{ id, authors, timestamp }` |
| `wordSimilarityVocab` | 词表 | 词语到ID的映射 |
| `wordSimilarityChunks` | 相似词分块 | 相似词数据 |

### 2.3 各模块缓存状态

| 模块 | 缓存方式 | 持久化 | 增量加载 |
|------|----------|--------|----------|
| `usePoems.ts` | IndexedDB | ✅ | ✅ |
| `useAuthors.ts` | IndexedDB | ✅ | ✅ |
| `useWordSimilarity.ts` | IndexedDB | ✅ | ✅ |
| `useSearchIndex.ts` | 内存 | ❌ | ❌ |
| `useWordcount.ts` | 无 | ❌ | ❌ |

---

## 3. 问题分析

### 3.1 核心问题

```
┌─────────────────────────────────────────────────────────────────┐
│                        问题优先级矩阵                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    高影响 ◄─────────────────────────────────► 低影响             │
│                                                                  │
│    ┌────────────────┐                    ┌────────────────┐      │
│    │ 🔴 高优先级    │                    │ 🟡 中优先级    │      │
│    │                │                    │                │      │
│    │ • useSearchIndex │                  │ • Schema 分散  │      │
│    │   无持久化      │                    │ • 缺乏通用API │      │
│    │                │                    │                │      │
│    └────────────────┘                    └────────────────┘      │
│                                                                  │
│    ┌────────────────┐                    ┌────────────────┐      │
│    │ 🟢 低优先级    │                    │ ⚪ 可延后      │      │
│    │                │                    │                │      │
│    │ • 代码重复    │                    │ • 监控告警    │      │
│    │ • 错误处理    │                    │ • 性能优化    │      │
│    │                │                    │                │      │
│    └────────────────┘                    └────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 具体问题清单

| # | 问题 | 影响 | 解决难度 |
|---|------|------|----------|
| P1 | useSearchIndex 刷新后数据丢失 | 用户体验差 | 低 |
| P2 | 缓存策略不统一 | 维护困难 | 中 |
| P3 | loadChunk 模式重复 | 代码冗余 | 低 |
| P4 | 缺乏错误处理标准 | 稳定性 | 中 |
| P5 | 无存储配额管理 | 长期使用风险 | 中 |

### 3.3 技术债务

```typescript
// 问题代码示例：多处重复的 loadChunk 模式

// usePoems.ts
async function loadChunk(chunkId: number) {
  // 检查缓存
  const cached = await getFromIndexedDB(...)
  if (cached) return cached
  
  // 加载数据
  const data = await fetch(...)
  
  // 存储缓存
  await saveToIndexedDB(...)
  return data
}

// useAuthors.ts (几乎相同的逻辑)
async function loadChunk(chunkId: number) {
  const cached = await getFromIndexedDB(...)  // 重复
  if (cached) return cached
  
  const data = await fetch(...)  // 重复
  await saveToIndexedDB(...)  // 重复
  return data
}

// useWordSimilarity.ts (几乎相同的逻辑)
async function loadChunk(chunkId: number) {
  const cached = await getFromIndexedDB(...)  // 重复
  if (cached) return cached
  
  const data = await fetch(...)  // 重复
  await saveToIndexedDB(...)  // 重复
  return data
}
```

---

## 4. 架构设计

### 4.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              应用层                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  usePoems   │  │  useAuthors  │  │useSearchIndex│ │useWordcount │       │
│  │    V2       │  │     V2       │  │     V2       │  │     V2       │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                │                │                │                │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           缓存服务层 (useCacheV2)                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                      缓存 API                                        │     │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐         │     │
│  │  │ getCache  │ │ setCache  │ │ getChunk  │ │ setChunk  │  ...   │     │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘         │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                      存储管理层                                       │     │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐         │     │
│  │  │ Storage   │ │  Schema   │ │  Version  │ │  Query    │         │     │
│  │  │ Manager   │ │  Manager  │ │  Manager  │ │  Builder  │         │     │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘         │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IndexedDB                                         │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│  │    cache    │  │   chunks     │  │  metadata   │                        │
│  │  (通用KV)   │  │  (分块数据)  │  │  (元数据)   │                        │
│  └─────────────┘  └─────────────┘  └─────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 composables_v2 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         composables_v2                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        类型定义 (types.ts)                            │   │
│  │  PoemSummary | AuthorStats | WordCountItem | SearchResult           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      缓存服务 (useCacheV2.ts)                         │   │
│  │  getCache | setCache | getChunkedCache | setChunkedCache            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    元数据加载器 (useMetadataLoader.ts)               │   │
│  │  usePoemsMetadata | useAuthorsMetadata | useWordcountMetadata        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ usePoemsV2   │ │ useAuthorsV2  │ │useWordcountV2│ │useSearchIndex│      │
│  │              │ │              │ │              │ │     V2       │      │
│  │ • 过滤查询   │ │ • 按名查询   │ │ • 范围查询   │ │ • 批量搜索   │      │
│  │ • 统计      │ │ • 相似诗人   │ │ • 排名统计   │ │ • 多关键词   │      │
│  │ • 批量加载  │ │ • 词频统计   │ │ • 预加载    │ │ • 预加载    │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   useWordSimilarityV2                                 │   │
│  │  • 相似词查询 • 词频查询 • 批量查询                                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 设计原则

| 原则 | 说明 | 实践 |
|------|------|------|
| **单一职责** | 每个模块只做一件事 | 缓存归缓存，业务归业务 |
| **开闭原则** | 对扩展开放，对修改关闭 | 通过配置扩展新数据源 |
| **依赖倒置** | 依赖抽象，不依赖具体 | 使用接口类型定义 |
| **最少知识** | 模块间最小依赖 | 通过 composable 共享状态 |

---

## 5. 详细设计

### 5.1 统一 Schema 设计

```typescript
// 统一缓存 Schema

interface CacheItem<T = unknown> {
  key: string           // 缓存键: "storage:key"
  storage: string       // 存储区域: "poems", "authors" 等
  data: T              // 缓存数据
  timestamp: number    // 创建时间
  expireAt?: number   // 过期时间 (可选)
}

interface ChunkItem<T = unknown> {
  key: string         // "storage:chunk:id"
  storage: string     // 存储区域
  chunkId: number    // 分块 ID
  data: T            // 分块数据
  timestamp: number  // 创建时间
}

interface MetadataItem {
  storage: string           // 存储区域
  loadedChunkIds: number[] // 已加载的分块 ID 列表
  totalChunks?: number      // 总分块数
  timestamp: number        // 更新时间
}

interface UnifiedCacheSchema extends DBSchema {
  // 通用键值缓存
  cache: {
    key: string
    value: CacheItem
    indexes: { 'by-storage': string }
  }
  
  // 分块数据缓存
  chunks: {
    key: string
    value: ChunkItem
    indexes: { 'by-storage': string }
  }
  
  // 元数据存储
  metadata: {
    key: string
    value: MetadataItem
  }
}
```

### 5.2 存储区域定义

```typescript
// 存储区域常量

export const STORAGE = {
  POEMS: 'poems-v2',
  AUTHORS: 'authors-v2',
  WORDCOUNT: 'wordcount-v2',
  WORD_SIMILARITY: 'word-similarity-v2',
  POEM_INDEX: 'poem-index-v2'
} as const

export type StorageName = typeof STORAGE[keyof typeof STORAGE]
```

### 5.3 API 设计

#### 基础缓存操作

```typescript
// 基础缓存 API

interface CacheOptions {
  expire?: number    // 过期时间 (毫秒)
  storage?: string  // 存储区域
}

interface CacheStats {
  keys: number      // 缓存键数量
  size: number      // 估算大小 (字节)
  lastUpdate: number // 最后更新时间
}

// 获取缓存
function getCache<T>(storage: string, key: string): Promise<T | null>

// 设置缓存
function setCache<T>(storage: string, key: string, data: T, options?: CacheOptions): Promise<void>

// 删除缓存
function deleteCache(storage: string, key: string): Promise<boolean>

// 清空缓存
function clearCache(storage?: string): Promise<void>

// 获取缓存统计
function getCacheStats(storage?: string): Promise<CacheStats>
```

#### 分块缓存操作

```typescript
// 分块缓存 API

// 获取分块数据
function getChunkedCache<T>(storage: string, chunkId: number): Promise<T | null>

// 设置分块数据
function setChunkedCache<T>(storage: string, chunkId: number, data: T): Promise<void>

// 检查分块是否存在
function hasChunk(storage: string, chunkId: number): Promise<boolean>

// 获取所有已缓存的分块 ID
function getAllChunkIds(storage: string): Promise<number[]>

// 获取所有已缓存的分块数据
function getAllChunkedData<T>(storage: string): Promise<T[]>
```

#### 元数据操作

```typescript
// 元数据 API

// 设置元数据
function setMetadata(
  storage: string, 
  data: { loadedChunkIds: number[]; totalChunks?: number }
): Promise<void>

// 获取元数据
function getMetadata(storage: string): Promise<MetadataItem | null>
```

---

## 6. 实施记录

### 6.1 实施时间线

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              实施时间线                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  2026-03-16                                                                  │
│     │                                                                        │
│     ├─► 14:00  创建 composables_v2/types.ts (类型定义)                       │
│     │                                                                        │
│     ├─► 14:30  创建 composables_v2/useCacheV2.ts (统一缓存)                  │
│     │                                                                        │
│     ├─► 15:00  创建 composables_v2/useMetadataLoader.ts (元数据加载器)       │
│     │                                                                        │
│     ├─► 15:30  创建 composables_v2/usePoemsV2.ts (诗歌增强)                  │
│     │                                                                        │
│     ├─► 16:00  创建 composables_v2/useAuthorsV2.ts (诗人增强)                │
│     │                                                                        │
│     ├─► 16:30  创建 composables_v2/useWordcountV2.ts (统计增强)              │
│     │                                                                        │
│     ├─► 17:00  创建 composables_v2/useSearchIndexV2.ts (搜索增强)            │
│     │                                                                        │
│     └─► 17:30  创建 composables_v2/index.ts (统一导出)                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 创建的文件

```
web/src/composables_v2/
├── index.ts                    # 统一导出入口
├── types.ts                    # 类型定义 (62 行)
├── useCacheV2.ts              # 统一缓存服务 (198 行)
├── useMetadataLoader.ts        # 元数据加载器 (183 行)
├── usePoemsV2.ts              # 诗歌数据管理 (217 行)
├── useAuthorsV2.ts            # 诗人数据管理 (186 行)
├── useWordcountV2.ts          # 字词统计 (155 行)
├── useSearchIndexV2.ts        # 搜索索引 (215 行)
└── useWordSimilarityV2.ts     # 词语相似度 (235 行)

总计: 1,451 行新代码
```

### 6.3 数据源配置

```typescript
// 元数据加载配置

const METADATA_CONFIGS = {
  poems: {
    storageName: 'poems-index',
    url: 'data/preprocessed/poems_chunk_meta.json',
    // 返回 PoemsIndex
  },
  authors: {
    storageName: 'authors-index', 
    url: 'data/author_v2/authors-meta.json',
    // 返回 AuthorsIndex
  },
  wordcount: {
    storageName: 'wordcount-meta',
    url: 'data/wordcount_v2/meta.json',
    // 返回 WordCountMeta
  },
  wordSimilarity: {
    storageName: 'word-similarity-meta',
    url: 'data/word_similarity_v3/metadata.json',
    // 返回 WordSimilarityMetadata
  },
  poemIndex: {
    storageName: 'poem-index-manifest',
    url: 'data/poem_index/manifest.json',
    // 返回 PoemIndexManifest
  }
}
```

---

## 7. API 参考

### 7.1 usePoemsV2

```typescript
// 诗歌数据管理

const poems = usePoemsV2()

// 属性
poems.metadata          // 元数据
poems.totalPoems       // 诗歌总数
poems.totalChunks      // 分块总数
poems.dynasties        // 朝代列表
poems.genres           // 体裁列表

// 方法
await poems.loadMetadata()                    // 加载元数据
await poems.loadChunkSummaries(id)           // 加载摘要分块
await poems.loadChunkDetails(id)              // 加载详情分块
await poems.getPoemById(id)                   // 获取单首诗

// 查询
await poems.queryPoems(filter, page, pageSize)      // 通用查询
await poems.getPoemsByDynasty(dynasty)             // 按朝代查询
await poems.getPoemsByGenre(genre)                 // 按体裁查询
await poems.searchPoems(keyword)                    // 搜索诗歌

// 统计
poems.getChunkStats()    // 获取分块统计

// 缓存
await poems.preloadChunks(ids)  // 预加载分块
await poems.clearCache()        // 清除缓存
```

### 7.2 useAuthorsV2

```typescript
// 诗人数据管理

const authors = useAuthorsV2()

// 查询
await authors.getAuthorByName(name)           // 按名字查询
await authors.queryAuthors(filter)            // 过滤查询
await authors.getTopAuthors(limit)            // 获取TOP诗人
await authors.getSimilarAuthors(name)         // 获取相似诗人

// 统计
await authors.getAuthorWordFrequency(name)    // 词频统计
await authors.getAuthorPoemTypes(name)         // 诗词类型统计
```

### 7.3 useWordcountV2

```typescript
// 字词统计

const wordcount = useWordcountV2()

// 查询
await wordcount.getWordCounts(start, end)     // 范围查询
await wordcount.getTopWords(n)                 // TOP N 查询
await wordcount.getWordsByChunk(chunkId)       // 按分块查询
await wordcount.searchWord(word)               // 单词查询

// 统计
await wordcount.getWordStats()                 // 获取详细统计

// 工具
await wordcount.getChunkByRank(rank)           // 根据排名获取分块ID
await wordcount.getRankRangeForChunk(id)      // 获取分块的排名范围
```

### 7.4 useSearchIndexV2

```typescript
// 搜索索引

const search = useSearchIndexV2()

// 搜索
await search.searchPoems(query, page, pageSize)                    // 搜索诗歌
await search.searchByKeyword(keyword, options)                      // 关键词搜索
await search.searchMultipleKeywords(keywords, options)              // 多关键词搜索
await search.getPoemsByAuthor(author, limit)                        // 按作者搜索
await search.getPoemsByDynasty(dynasty, page, pageSize)            // 按朝代搜索
await search.getPoemsByPrefix(prefix, limit)                        // 按前缀搜索

// 预加载
await search.preloadPrefixes(prefixes)      // 预加载前缀
```

### 7.5 useWordSimilarityV2

```typescript
// 词语相似度

const wordSim = useWordSimilarityV2()

// 初始化
await wordSim.initialize()                   // 初始化词表

// 查询
await wordSim.hasWord(word)                  // 检查词是否存在
await wordSim.getSimilarWords(word, options) // 获取相似词
await wordSim.getWordFrequency(word)         // 获取词频
await wordSim.getWordInfo(word)              // 获取完整信息
await wordSim.searchSimilarWords(words)      // 批量搜索
```

---

## 8. 缓存策略

### 8.1 过期策略

```typescript
// 自动清理过期缓存

async function cleanupExpired(): Promise<number> {
  const db = await getDB()
  const tx = db.transaction('cache', 'readwrite')
  const store = tx.objectStore('cache')
  const now = Date.now()
  
  let deleted = 0
  let cursor = await store.openCursor()
  
  while (cursor) {
    const item = cursor.value
    if (item.expireAt && item.expireAt < now) {
      await cursor.delete()
      deleted++
    }
    cursor = await cursor.continue()
  }
  
  await tx.done
  console.log(`[Cache] Cleaned up ${deleted} expired items`)
  return deleted
}

// 启动定期清理 (每5分钟)
setInterval(cleanupExpired, 5 * 60 * 1000)
```

### 8.2 存储配额管理

```typescript
// 检查存储空间

async function checkStorageQuota(): Promise<{ used: number; quota: number; percent: number }> {
  if (navigator.storage?.estimate) {
    const estimate = await navigator.storage.estimate()
    const used = estimate.usage || 0
    const quota = estimate.quota || 0
    return {
      used,
      quota,
      percent: quota > 0 ? (used / quota) * 100 : 0
    }
  }
  return { used: 0, quota: 0, percent: 0 }
}

// 使用示例
const { used, quota, percent } = await checkStorageQuota()
console.log(`Storage: ${(used / 1024 / 1024).toFixed(2)} MB / ${(quota / 1024 / 1024).toFixed(2)} MB (${percent.toFixed(1)}%)`)

// 空间不足时清理
async function evictIfNeeded(): Promise<void> {
  const { percent } = await checkStorageQuota()
  
  if (percent > 80) {
    console.warn('[Cache] Storage usage high, evicting oldest data...')
    // 按时间排序删除最旧的数据
    // ...
  }
}
```

### 8.3 缓存键命名规范

```
┌─────────────────────────────────────────────────────────────────┐
│                        缓存键命名规范                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  通用缓存:  {storage}:{key}                                      │
│     示例:  poems:metadata, authors:vocab                         │
│                                                                  │
│  分块缓存: {storage}:chunk:{chunkId}                            │
│     示例:  poems:chunk:0, authors:chunk:100                      │
│                                                                  │
│  元数据:   {storage}                                            │
│     示例:  poems, authors, wordcount                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. 测试策略

### 9.1 单元测试

```typescript
// useCacheV2.test.ts

import { describe, it, expect, beforeEach } from 'vitest'
import { getCache, setCache, deleteCache, clearCache } from './useCacheV2'

describe('useCacheV2', () => {
  beforeEach(async () => {
    await clearCache('test')
  })
  
  it('should set and get cache', async () => {
    await setCache('test', 'key1', { foo: 'bar' })
    const result = await getCache('test', 'key1')
    expect(result).toEqual({ foo: 'bar' })
  })
  
  it('should return null for non-existent key', async () => {
    const result = await getCache('test', 'nonexistent')
    expect(result).toBeNull()
  })
  
  it('should delete cache', async () => {
    await setCache('test', 'key1', 'value')
    await deleteCache('test', 'key1')
    const result = await getCache('test', 'key1')
    expect(result).toBeNull()
  })
})
```

### 9.2 集成测试

```typescript
// usePoemsV2.integration.test.ts

import { describe, it, expect } from 'vitest'
import { usePoemsV2 } from './usePoemsV2'

describe('usePoemsV2 Integration', () => {
  it('should load and cache poems', async () => {
    const poems = usePoemsV2()
    
    await poems.loadMetadata()
    const result = await poems.queryPoems({ dynasty: '唐' }, 1, 10)
    
    expect(result.poems).toBeDefined()
    expect(result.total).toBeGreaterThan(0)
  })
})
```

---

## 10. 版本迁移

### 10.1 迁移策略

```
┌─────────────────────────────────────────────────────────────────┐
│                        迁移策略                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: 现有模块保持不变                                       │
│  ─────────────────────────────                                   │
│  • usePoems, useAuthors, useWordSimilarity 继续使用旧代码        │
│  • 新功能使用 composables_v2                                    │
│                                                                  │
│  Phase 2: 逐步迁移                                               │
│  ────────────────────────                                       │
│  • 新页面使用 composables_v2                                     │
│  • 旧页面渐进式迁移                                              │
│                                                                  │
│  Phase 3: 统一废弃                                                │
│  ────────────────────                                           │
│  • 旧模块标记 @deprecated                                        │
│  • 文档迁移指南                                                   │
│  • 最终移除                                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 迁移检查表

```markdown
- [ ] 新组件使用 composables_v2
- [ ] 导入路径更新为 `@/composables_v2`
- [ ] 类型接口保持兼容
- [ ] 测试用例通过
- [ ] 旧代码标记 @deprecated
- [ ] 更新相关文档
```

---

## 11. 检查清单

### 11.1 完成状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 创建 `useCacheV2.ts` | ✅ | 统一缓存服务 |
| 改造 `useSearchIndex.ts` | ✅ | 使用 IndexedDB |
| 创建 `composables_v2` | ✅ | 全新框架 |
| 文档更新 | ✅ | 本文档 |

### 11.2 后续任务

| 项目 | 优先级 | 状态 |
|------|--------|------|
| 旧模块迁移到 v2 | 中 | 待定 |
| 添加单元测试 | 中 | 待定 |
| 性能监控 | 低 | 待定 |
| 错误边界处理 | 中 | 待定 |

---

## 附录 A: 文件位置

| 文件 | 路径 |
|------|------|
| 统一缓存 (v2) | `web/src/composables_v2/useCacheV2.ts` |
| 元数据加载器 | `web/src/composables_v2/useMetadataLoader.ts` |
| 诗歌模块 (v2) | `web/src/composables_v2/usePoemsV2.ts` |
| 诗人模块 (v2) | `web/src/composables_v2/useAuthorsV2.ts` |
| 字词统计 (v2) | `web/src/composables_v2/useWordcountV2.ts` |
| 搜索索引 (v2) | `web/src/composables_v2/useSearchIndexV2.ts` |
| 词语相似度 (v2) | `web/src/composables_v2/useWordSimilarityV2.ts` |
| 类型定义 | `web/src/composables_v2/types.ts` |
| 统一导出 | `web/src/composables_v2/index.ts` |

---

## 附录 B: 使用示例

```typescript
// 完整使用示例

import { 
  usePoemsV2, 
  useAuthorsV2, 
  useWordcountV2, 
  useSearchIndexV2,
  useWordSimilarityV2 
} from '@/composables_v2'

async function main() {
  // 1. 诗歌查询示例
  const poems = usePoemsV2()
  await poems.loadMetadata()
  
  const tangPoems = await poems.queryPoems({ 
    dynasty: '唐', 
    search: '春' 
  }, 1, 20)
  
  console.log(`找到 ${tangPoems.filteredTotal} 首唐诗`)
  
  // 2. 诗人查询示例
  const authors = useAuthorsV2()
  const liBai = await authors.getAuthorByName('李白')
  
  if (liBai) {
    console.log(`李白共有 ${liBai.poem_count} 首诗`)
    console.log('相似诗人:', liBai.similar_authors.slice(0, 5))
  }
  
  // 3. 字词统计示例
  const wordcount = useWordcountV2()
  const topWords = await wordcount.getTopWords(100)
  
  console.log('TOP 10 高频词:', topWords.slice(0, 10))
  
  // 4. 搜索示例
  const search = useSearchIndexV2()
  const results = await search.searchPoems('明月', 1, 10)
  
  console.log(`搜索到 ${results.total} 条结果`)
  
  // 5. 词语相似度示例
  const wordSim = useWordSimilarityV2()
  await wordSim.initialize()
  
  const similar = await wordSim.getSimilarWords('春江', { 
    minSimilarity: 0.7 
  })
  
  console.log('与"春江"相似的词:', similar.map(s => s.word))
}

main()
```

---

*文档最后更新: 2026-03-16*
