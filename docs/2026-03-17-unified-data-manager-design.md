# 统一数据管理系统设计文档

> 日期: 2026-03-17  
> 更新: 2026-03-22  
> 设计目标: 构建一个高性能、可扩展、统一的数据管理系统，支持多种数据类型和存储策略

## 1. 当前系统分析

### 1.1 现有组件

| 组件 | 后端格式 | 前端处理 | 存储格式 | 用途 |
|------|---------|---------|---------|------|
| usePoemsV2 | CSV (.csv) | 下载后解析 CSV → 存入 IndexedDB | JSON | 诗词列表/详情 |
| useAuthorsV2 | FBS (.fbs) | 下载后解析 FBS → 存入 IndexedDB | JSON | 诗人数据 |
| useWordcountV2 | JSON (.json) | 直接存入 IndexedDB | JSON | 词频统计 |
| useWordSimilarityV2 | FBS (.bin) | 下载后解析 FBS → 存入 IndexedDB | JSON | 词境数据 |
| useSearchIndexV2 | JSON (.json) | 直接存入 IndexedDB | JSON | 诗词索引 |
| useKeywordIndex | JSON (.json) | 下载后存入 IndexedDB | JSON | 关键词索引 |

### 1.2 完整数据流分析

#### 1. 诗词 (Poems) - usePoemsV2
```
数据源: data/preprocessed/poems_chunk_*.csv
  ↓ fetch CSV
  ↓ parseCsvLine() 解析
  ↓ setChunkedCache() 存入 IndexedDB (poems-summary-v2 / poems-detail-v2)
  ↓ setMetadata() 记录已加载 chunk
存储: poems-summary-v2 / poems-detail-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 2. 诗人 (Authors) - useAuthorsV2
```
数据源: data/author_v2/author_chunk_*.fbs
  ↓ fetch FBS
  ↓ flatbuffers 解析
  ↓ setChunkedCache() 存入 IndexedDB (authors-v2)
  ↓ setMetadata() 记录已加载 chunk
存储: authors-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 3. 词频 (WordCount) - useWordcountV2
```
数据源: data/wordcount_v2/chunk_*.json
  ↓ fetch JSON
  ↓ setChunkedCache() 存入 IndexedDB (wordcount-v2)
  ↓ setMetadata() 记录已加载 chunk
存储: wordcount-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 4. 词境 (WordSimilarity) - useWordSimilarityV2
```
数据源: data/word_similarity_v3/word_chunk_*.bin
  ↓ fetch FBS
  ↓ parseWordSimilarityChunk() 解析
  ↓ setChunkedCache() 存入 IndexedDB (word-similarity-v2)
  ↓ setMetadata() 记录已加载 chunk
存储: word-similarity-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 5. 诗词索引 (PoemIndex) - useSearchIndexV2
```
数据源: data/poem_index/poems_*.json
  ↓ fetch JSON
  ↓ setChunkedCache() 存入 IndexedDB (poem-index-v2)
  ↓ setCache() 记录已加载 prefixes
  ↓ setMetadata() 记录已加载 chunk (2026-03-22 新增)
存储: poem-index-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 6. 关键词索引 (KeywordIndex) - useKeywordIndex
```
数据源: results/keyword_index/keyword_*.json
  ↓ fetch JSON
  ↓ setChunkedCache() 存入 IndexedDB (keyword-index-v2)
  ↓ setMetadata() 记录已加载 chunk
存储: keyword-index-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

### 1.3 数据文件位置

| 数据类型 | 目录 | 文件模式 | Storage Name |
|---------|------|---------|-------------|
| 诗词摘要 | data/preprocessed/ | poems_chunk_*.csv | poems-summary-v2 |
| 诗词详情 | data/preprocessed/ | poems_chunk_*.csv | poems-detail-v2 |
| 诗词索引 | data/preprocessed/ | poems_chunk_meta.json | poems-v2 (metadata only) |
| 诗人 | data/author_v2/ | author_chunk_*.fbs | authors-v2 |
| 词频 | data/wordcount_v2/ | chunk_*.json | wordcount-v2 |
| 词境 | data/word_similarity_v3/ | word_chunk_*.bin | word-similarity-v2 |
| 诗词索引 | data/poem_index/ | poems_*.json | poem-index-v2 |
| 关键词索引 | results/keyword_index/ | keyword_*.json | keyword-index-v2 |

### 1.4 当前问题与修复

#### 已修复问题 (2026-03-22)

1. **poems-v2 显示 0 B 问题** ✅
   - 原因: 诗词数据实际存储在 `poems-summary-v2` 和 `poems-detail-v2`，但 metadata 只记录在 `poems-v2`
   - 修复: 在 `usePoemsV2.ts` 中为 `POEMS_SUMMARY_STORAGE` 和 `POEMS_DETAIL_STORAGE` 添加 `setMetadata` 调用

2. **poem-index-v2 不显示问题** ✅
   - 原因: `useSearchIndexV2.ts` 没有调用 `setMetadata`，导致 `getAllStorageStats()` 无法获取该 storage
   - 修复: 在 `loadPoemChunk` 函数中添加 `setMetadata(POEM_INDEX_STORAGE, ...)`

#### 仍存在的问题

1. **存储状态不透明**: 无法直观看到 IndexedDB 里存的是什么格式
2. **无法区分来源**: 不知道当前数据是从网络还是缓存来的
3. **FBS 解析性能**: 首次加载 FBS 数据仍需要解析时间

---

## 2. 存储系统架构

### 2.1 IndexedDB Schema

```typescript
// 统一存储 schema (cache-v2)
interface UnifiedCacheSchema {
  // 元数据表 - 记录每个 storage 的加载状态
  'metadata': {
    key: string  // storage name (e.g., 'poems-summary-v2')
    value: {
      storage: string
      loadedChunkIds: number[]
      totalChunks?: number
      timestamp: number
    }
  }
  
  // 分块数据表 - 存储 chunk 数据
  'chunks': {
    key: string  // `${storage}:chunk:${chunkId}`
    value: {
      key: string
      storage: string
      chunkId: number | string
      data: any
      timestamp: number
      sourceUrl?: string  // 2026-03-22 新增: 源文件路径
    }
    indexes: { 'by-storage': string }
  }
  
  // 缓存项表 - 存储非 chunk 数据 (如 vocab, metadata 等)
  'cache': {
    key: string  // `${storage}:${key}`
    value: {
      key: string
      storage: string
      data: any
      timestamp: number
      expireAt?: number
      sourceUrl?: string  // 2026-03-22 新增: 源文件路径
    }
    indexes: { 'by-storage': string }
  }
}
```

### 2.2 Storage 命名规范

| 数据类型 | Storage Name | 说明 |
|---------|-------------|------|
| 诗词摘要 | poems-summary-v2 | 诗词列表数据 |
| 诗词详情 | poems-detail-v2 | 诗词完整数据 |
| 诗词索引 | poems-v2 | 仅 metadata |
| 诗人 | authors-v2 | 诗人数据 |
| 词频 | wordcount-v2 | 词频统计 |
| 词境 | word-similarity-v2 | 词向量数据 |
| 诗词索引 | poem-index-v2 | ID 搜索索引 |
| 关键词索引 | keyword-index-v2 | 关键词搜索索引 |

---

## 3. 核心 API 设计

### 3.1 Cache API

```typescript
// useCacheV2.ts

// 存储选项
interface CacheOptions {
  expire?: number       // 过期时间 (ms)
  storage?: string      // 存储名称
  sourceUrl?: string    // 2026-03-22 新增: 源文件路径
}

// 分块缓存选项
interface ChunkCacheOptions {
  sourceUrl?: string    // 2026-03-22 新增: 源文件路径
}

// 存储普通缓存项
async function setCache<T>(
  storage: string, 
  key: string, 
  data: T, 
  options?: CacheOptions
): Promise<void>

// 获取普通缓存项
async function getCache<T>(storage: string, key: string): Promise<T | null>

// 存储分块数据
async function setChunkedCache<T>(
  storage: string, 
  chunkId: number | string, 
  data: T, 
  options?: ChunkCacheOptions
): Promise<void>

// 获取分块数据
async function getChunkedCache<T>(storage: string, chunkId: number | string): Promise<T | null>

// 存储 metadata
async function setMetadata(
  storage: string, 
  data: Omit<MetadataItem, 'storage' | 'timestamp'>
): Promise<void>

// 获取 metadata
async function getMetadata(storage: string): Promise<MetadataItem | null>

// 获取存储统计
async function getStorageStats(storage: string): Promise<StorageStats>

// 获取所有存储统计
async function getAllStorageStats(): Promise<StorageStats[]>

// 清空存储
async function clearStorage(storage: string): Promise<void>
```

### 3.2 StorageStats 接口

```typescript
interface StorageStats {
  storage: string
  chunkCount: number
  cacheCount: number
  totalSize: number
  chunks: Array<{
    chunkId: number | string
    size: number
    timestamp: number
    sourceUrl?: string  // 2026-03-22 新增
  }>
  caches: Array<{
    key: string
    size: number
    timestamp: number
    sourceUrl?: string  // 2026-03-22 新增
  }>
}
```

---

## 4. 数据管理组件

### 4.1 DataStorage.vue

功能：展示所有存储的统计信息

**展示内容**:
- 浏览器存储概览 (IndexedDB, LocalStorage, SessionStorage, Cookies)
- 存储配额使用情况
- 各 storage 的分块数和缓存项数
- 分块和缓存项详情（支持显示 sourceUrl）

**操作**:
- 刷新统计
- 清空缓存（支持清空单个 storage）

### 4.2 存储状态监控

```typescript
interface BrowserStorageInfo {
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
```

---

## 5. 新增功能: 文件路径追踪 (sourceUrl)

### 5.1 功能说明

在存储详情中显示每个 chunk/cache 的源文件路径，便于追踪数据来源。

### 5.2 实现方式

```typescript
// 存储 chunk 时传入文件路径
await setChunkedCache(POEMS_SUMMARY_STORAGE, chunkNum, poems, {
  sourceUrl: `data/preprocessed/poems_chunk_${chunkId}.csv`
})

// 存储 cache 时传入文件路径
await setCache(POEM_INDEX_STORAGE, 'loaded-prefixes', prefixesArray, {
  sourceUrl: 'data/poem_index/manifest.json'
})
```

### 5.3 UI 展示

在 DataStorage.vue 的详情列表中：
- 分块列表显示 `sourceUrl`
- 缓存项列表显示 `sourceUrl`
- 使用等宽字体，过长路径自动截断并显示省略号

### 5.4 注意事项

- 现有已缓存的数据没有 `sourceUrl`
- 只有在重新加载数据并使用新的 API 存储时才会记录文件路径

---

## 6. 性能基准

| 操作 | 当前 | 目标 |
|------|------|------|
| 首次加载 WordSim chunk | 500-2000ms | 500-2000ms |
| 二次加载 WordSim chunk | < 50ms | < 50ms |
| DataDashboard 加载 | 200-500ms | < 200ms |
| 内存占用 (20万词) | ~100MB | < 100MB |

---

## 7. 相关文件位置

```
web/src/
├── composables/
│   ├── useCacheV2.ts          # 缓存层核心 API
│   ├── useMetadataLoader.ts   # 元数据加载
│   ├── usePoemsV2.ts          # 诗词数据管理
│   ├── useAuthorsV2.ts        # 诗人数据管理
│   ├── useWordcountV2.ts      # 词频数据管理
│   ├── useWordSimilarityV2.ts # 词境数据管理
│   ├── useSearchIndexV2.ts    # 诗词索引管理
│   └── useKeywordIndex.ts     # 关键词索引管理
├── components/
│   └── data/
│       └── DataStorage.vue    # 存储状态展示组件
└── views/
    └── DataStorageView.vue    # 存储管理页面
```

---

## 8. 关键依赖

- `flatbuffers`: FBS 解析
- `idb`: IndexedDB 封装
- `naive-ui`: UI 组件

---

## 9. 更新日志

### 2026-03-22

#### 修复
- 修复 poems-v2 显示 0 B 问题
- 修复 poem-index-v2 不显示问题
- 更新 DataStorage 清空缓存逻辑

#### 新增
- 添加 sourceUrl 支持，可在存储详情中显示源文件路径
- 扩展 CacheItem 和 ChunkItem 接口
- 更新 setCache 和 setChunkedCache API
- 更新 StorageStats 接口
- 更新 DataStorage.vue UI

