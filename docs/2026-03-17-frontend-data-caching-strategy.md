# 前端数据缓存与预处理架构设计

**日期**: 2026-03-17
**版本**: v1.0
**状态**: 设计提案
**目标**: 解决大规模静态数据在前端的高效缓存、索引和搜索问题

---

## 📋 目录

1. [现状分析](#1-现状分析)
2. [核心痛点](#2-核心痛点)
3. [2026年SOTA技术选型](#3-2026年sota技术选型)
4. [架构设计方案](#4-架构设计方案)
5. [数据模型重构](#5-数据模型重构)
6. [缓存策略详解](#6-缓存策略详解)
7. [搜索索引优化](#7-搜索索引优化)
8. [实施路线图](#8-实施路线图)

---

## 1. 现状分析

### 1.1 数据资产总览

根据 [deploy-pages.yml](../.github/workflows/deploy-pages.yml) 和代码分析，系统目前拥有以下数据：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据资产清单                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📚 诗词数据 (poem_index)                                                    │
│  ├── 总量: 332,712 首诗                                                      │
│  ├── 分块: 257 个前缀分块 (prefixLength=2)                                    │
│  ├── 格式: JSON                                                             │
│  └── 内容: {id, title, author, dynasty, genre}                              │
│                                                                             │
│  👤 诗人数据 (author_v2)                                                     │
│  ├── 总量: 13,206 位诗人                                                     │
│  ├── 分块: 223 个 FlatBuffers 文件                                           │
│  ├── 格式: FlatBuffers (.fbs)                                               │
│  └── 内容: 诗人统计、诗列表、词频、相似诗人                                    │
│                                                                             │
│  🔤 词相似度 (word_similarity_v3)                                            │
│  ├── 分块: 231 个 FlatBuffers 文件                                           │
│  ├── 格式: FlatBuffers (.bin)                                               │
│  └── 内容: 词ID、词频、相似词列表                                             │
│                                                                             │
│  🏷️ 关键词索引 (keyword_index)                                               │
│  ├── 分块: 13 个 JSON 文件                                                   │
│  ├── 格式: JSON                                                             │
│  └── 内容: {keyword: [poem_id1, poem_id2, ...]}                             │
│                                                                             │
│  📊 词频统计 (wordcount_v2)                                                  │
│  ├── 格式: JSON                                                             │
│  └── 内容: 全局词频统计                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 现有前端架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          现有前端数据流                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│   │  Vue Views  │    │  Vue Views  │    │  Vue Views  │    │  Vue Views  │ │
│   │  (诗词列表)  │    │  (诗人详情)  │    │  (词云页面)  │    │  (搜索结果)  │ │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘ │
│          │                  │                  │                  │        │
│          ▼                  ▼                  ▼                  ▼        │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│   │ usePoemsV2  │    │useAuthorsV2 │    │useWordcount │    │useSearchIndex│ │
│   │             │    │             │    │     V2      │    │     V2      │ │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘ │
│          │                  │                  │                  │        │
│          ▼                  ▼                  ▼                  ▼        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                     IndexedDB (useCacheV2)                          │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│   │  │  cache  │  │ chunks  │  │ metadata│  │  poems  │  │ authors │   │  │
│   │  │  store  │  │  store  │  │  store  │  │  store  │  │  store  │   │  │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ⚠️ 问题:                                                                  │
│   - 各 composable 独立管理缓存，缺乏统一协调                                  │
│   - keyword_index 未接入 IndexedDB，刷新丢失                                  │
│   - 搜索需要遍历所有 chunks，性能瓶颈                                         │
│   - 缺乏数据预热和预加载机制                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心痛点

### 2.1 搜索性能瓶颈

```typescript
// 当前搜索实现的问题
async function searchByKeyword(keyword: string) {
  const results = []
  const prefixes = Object.keys(manifest.prefixMap) // 257 个前缀
  
  for (const prefix of prefixes) {
    if (results.length >= limit) break
    
    const chunk = await loadPoemChunk(prefix) // 每次都要加载 chunk
    if (!chunk) continue
    
    // 遍历 chunk 内所有诗词
    for (const [id, poem] of chunk.entries()) {
      if (poem.title.includes(keyword) || poem.author.includes(keyword)) {
        results.push(poem)
      }
    }
  }
  return results
}
// 时间复杂度: O(N * M) - N=257 chunks, M=平均每个chunk的诗词数
```

**问题分析**:
- 全量扫描 257 个 chunk，即使只需要 10 条结果
- 无法利用索引，每次搜索都是线性扫描
- 没有倒排索引支持关键词快速定位

### 2.2 数据冗余与不一致

```
诗词详情存储在两个地方:
├── poem_index/poems_xx.json     (搜索用摘要)
├── preprocessed/*.json          (详情数据)
└── author_v2/*.fbs              (诗人包含的诗列表)

问题:
- 同一首诗的元数据分散在多个文件
- 需要多次请求才能组装完整信息
- 缓存策略不统一，容易过期不一致
```

### 2.3 内存与缓存管理

```
当前缓存问题:
├── 没有 LRU 淘汰机制
├── 所有加载的数据常驻内存
├── IndexedDB 没有版本管理和迁移策略
└── 缺乏存储配额监控和优雅降级
```

---

## 3. 2026年SOTA技术选型

### 3.1 浏览器存储技术对比

| 技术 | 容量 | 特点 | 适用场景 | 2026状态 |
|------|------|------|----------|----------|
| **IndexedDB** | ~60% 磁盘 | 结构化、索引、事务 | 主存储 | ✅ 成熟 |
| **Cache API** | 共享 | Service Worker 专用 | 离线缓存 | ✅ 成熟 |
| **OPFS** | ~60% 磁盘 | 文件系统 API | 大文件存储 | ✅ 推荐 |
| **SQLite WASM** | ~2GB | SQL 查询、FTS5 | 复杂查询 | 🚀 新兴 |
| **Vector DB (客户端)** | 内存限制 | 语义搜索 | AI 应用 | 🚀 新兴 |

### 3.2 推荐技术栈

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        2026 推荐技术栈                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🏗️ 核心存储层                                                               │
│  ├── IndexedDB (主存储) - idb 库封装                                         │
│  │   └── 诗词、诗人、词频等结构化数据                                         │
│  │                                                                          │
│  ├── OPFS (大文件存储) - 可选                                                │
│  │   └── FlatBuffers 原始二进制文件缓存                                       │
│  │                                                                          │
│  └── SQLite WASM (搜索索引) - sql.js 或 absurd-sql                           │
│      └── 倒排索引、全文搜索、复杂查询                                          │
│                                                                             │
│  🔍 搜索层                                                                   │
│  ├── FlexSearch / MiniSearch (轻量全文搜索)                                  │
│  │   └── 客户端构建内存索引，毫秒级搜索                                        │
│  │                                                                          │
│  └── 自定义倒排索引 (针对中文优化)                                            │
│      └── 基于 keyword_index 构建更细粒度索引                                  │
│                                                                             │
│  📦 数据序列化                                                                │
│  ├── FlatBuffers (保持现状)                                                  │
│  │   └── 零拷贝解析，适合大数据量                                              │
│  │                                                                          │
│  ├── MessagePack (替代 JSON)                                                 │
│  │   └── 更小体积，更快解析                                                   │
│  │                                                                          │
│  └── Arrow IPC (可选) - 针对列式数据分析                                       │
│                                                                             │
│  🚀 性能优化                                                                  │
│  ├── Web Workers - 数据解析 offload                                          │
│  ├── Compression Streams API - 传输压缩                                       │
│  └── Request Idle Callback - 后台预加载                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 为什么选这些技术

1. **SQLite WASM**: 2026年已经非常成熟，可以在浏览器中运行完整 SQL，支持 FTS5 全文搜索
2. **FlexSearch**: 比 Lunr.js 更快，支持中文，可以增量构建索引
3. **OPFS**: 现代浏览器支持，可以直接操作文件，避免 IndexedDB 的序列化开销
4. **MessagePack**: 比 JSON 快 5-10 倍解析，体积小 30-50%

---

## 4. 架构设计方案

### 4.1 目标架构

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            目标架构: 分层数据管理                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         应用层 (Vue Composables)                         │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │   │
│   │  │   usePoem   │  │  useAuthor  │  │  useSearch  │  │  useWordCloud   │ │   │
│   │  │   Store     │  │    Store    │  │    Store    │  │     Store       │ │   │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │   │
│   │         └─────────────────┴─────────────────┘                 │          │   │
│   │                           │                                   │          │   │
│   │                           ▼                                   ▼          │   │
│   │                  ┌─────────────────┐              ┌─────────────────┐    │   │
│   │                  │   DataManager   │              │  IndexManager   │    │   │
│   │                  │   (统一数据管理)  │              │   (搜索索引管理) │    │   │
│   │                  └────────┬────────┘              └─────────────────┘    │   │
│   └───────────────────────────┼─────────────────────────────────────────────┘   │
│                               │                                                 │
│   ┌───────────────────────────▼─────────────────────────────────────────────┐   │
│   │                        存储抽象层 (Storage Adapters)                      │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │   │
│   │  │  IndexedDB  │  │    OPFS     │  │ SQLite WASM │  │  Memory Cache   │ │   │
│   │  │   Adapter   │  │   Adapter   │  │   Adapter   │  │    (LRU)        │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         数据层 (Data Sources)                            │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │   │
│   │  │ Static JSON │  │ FlatBuffers │  │ Search Index│  │  Pre-computed   │ │   │
│   │  │   (HTTP)    │  │   (HTTP)    │  │   (HTTP)    │  │    Bundles      │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 核心组件设计

#### 4.2.1 DataManager - 统一数据管理器

```typescript
// 统一数据访问接口
interface DataManager {
  // 诗词数据
  poems: {
    getById(id: string): Promise<PoemDetail | null>
    getByAuthor(author: string): Promise<PoemSummary[]>
    getByKeyword(keyword: string): Promise<PoemSummary[]>
    search(query: SearchQuery): Promise<SearchResult>
  }
  
  // 诗人数据
  authors: {
    getByName(name: string): Promise<AuthorStats | null>
    getAll(options: PaginationOptions): Promise<AuthorQueryResult>
    getSimilar(author: string): Promise<SimilarAuthor[]>
  }
  
  // 词数据
  words: {
    getFrequency(word: string): Promise<number>
    getSimilar(word: string): Promise<SimilarWord[]>
    getCloudData(dynasty?: string): Promise<WordCloudItem[]>
  }
  
  // 缓存管理
  cache: {
    warmUp(type: DataType): Promise<void>
    clear(type?: DataType): Promise<void>
    getStats(): CacheStats
  }
}
```

#### 4.2.2 IndexManager - 搜索索引管理器

```typescript
// 多层级索引策略
interface IndexManager {
  // L1: 内存中的倒排索引 (关键词 -> 诗词ID列表)
  memoryIndex: {
    keywordToPoems: Map<string, string[]>
    authorToPoems: Map<string, string[]>
    dynastyToPoems: Map<string, string[]>
  }
  
  // L2: SQLite FTS5 全文索引
  ftsIndex: {
    search(text: string): Promise<SearchResult[]>
    searchWithHighlight(text: string): Promise<HighlightedResult[]>
  }
  
  // L3: 原始数据回退
  fallback: {
    scanChunks(query: string): Promise<SearchResult[]>
  }
}
```

---

## 5. 数据模型重构

### 5.1 统一实体模型

```typescript
// 核心实体定义

interface Poem {
  id: string                    // 唯一标识 (MD5)
  title: string                 // 标题
  author: string                // 作者名
  dynasty: string               // 朝代
  genre: string                 // 体裁 (诗/词)
  content: {                    // 内容
    sentences: string[]         // 句子列表
    words: string[]             // 分词结果
  }
  metadata: {                   // 元数据
    meterPattern?: string       // 格律
    tags: string[]              // 标签
    keywords: string[]          // 关键词 (从 TF-IDF 提取)
  }
  stats: {                      // 统计
    wordCount: number
    charCount: number
  }
  // 关联 (存储ID，懒加载)
  related: {
    similarPoems: string[]      // 相似诗词ID
    sameTheme: string[]         // 同主题诗词ID
  }
}

interface Author {
  name: string                  // 姓名 (唯一标识)
  dynasty: string               // 朝代
  stats: {                      // 统计
    poemCount: number
    poemTypes: Record<string, number>
    wordFrequency: Map<string, number>
  }
  works: string[]               // 作品ID列表 (分页加载)
  profile: {                    // 画像
    topWords: string[]          // 高频词
    meterPatterns: string[]     // 常用格律
    similarAuthors: string[]    // 相似诗人
  }
}

interface Word {
  text: string                  // 词文本
  frequency: number             // 全局频次
  poems: string[]               // 出现的诗词ID (采样)
  similar: Array<{              // 相似词
    word: string
    similarity: number
  }>
  evolution?: {                 // 时代演变 (可选)
    byDynasty: Record<string, number>
  }
}
```

### 5.2 存储 Schema 设计

```typescript
// IndexedDB Schema (使用 idb 库)

interface PoetryDB extends DBSchema {
  // 诗词主表
  poems: {
    key: string
    value: Poem
    indexes: {
      'by-author': string
      'by-dynasty': string
      'by-genre': string
    }
  }
  
  // 诗人表
  authors: {
    key: string
    value: Author
    indexes: {
      'by-dynasty': string
      'by-poem-count': number
    }
  }
  
  // 词表
  words: {
    key: string
    value: Word
    indexes: {
      'by-frequency': number
    }
  }
  
  // 倒排索引 (关键词 -> 诗词ID)
  invertedIndex: {
    key: string           // keyword:poem | keyword:author | keyword:dynasty
    value: {
      type: 'poem' | 'author' | 'dynasty'
      keyword: string
      ids: string[]       // 诗词ID列表
      count: number
    }
  }
  
  // 分块元数据
  chunks: {
    key: string           // storage:chunkId
    value: {
      storage: string
      chunkId: string
      loadedAt: number
      itemCount: number
      size: number        // 字节数
    }
  }
  
  // 缓存统计
  cacheStats: {
    key: string
    value: {
      totalSize: number
      itemCount: number
      lastCleanup: number
    }
  }
}
```

---

## 6. 缓存策略详解

### 6.1 三级缓存架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          三级缓存架构                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  L1: 内存缓存 (LRU)                                                          │
│  ├── 容量: 1000 条诗词 / 100 位诗人                                          │
│  ├── 策略: 最近最少使用淘汰                                                  │
│  └── 内容: 当前页面数据、用户浏览历史                                         │
│                                                                             │
│  L2: IndexedDB (持久化)                                                      │
│  ├── 容量: 约 500MB (浏览器限制)                                             │
│  ├── 策略: 分块存储，按需加载                                                 │
│  └── 内容: 所有访问过的诗词、索引数据                                         │
│                                                                             │
│  L3: HTTP Cache / Service Worker                                             │
│  ├── 容量: 由浏览器管理                                                      │
│  ├── 策略: immutable 资源长期缓存                                             │
│  └── 内容: 原始数据文件 (JSON/FlatBuffers)                                   │
│                                                                             │
│  数据流:                                                                    │
│  读取: L1 → L2 → L3 → 网络                                                   │
│  写入: 网络 → L3 → L2 → L1                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 智能预加载策略

```typescript
// 基于用户行为的预加载

class SmartPreloader {
  // 1. 页面级预加载
  async preloadForPage(route: string) {
    switch(route) {
      case '/poems':
        // 预加载诗词列表第一页 + 常用筛选条件数据
        await Promise.all([
          this.dataManager.poems.getPage(1),
          this.dataManager.getDynasties(),
          this.dataManager.getGenres()
        ])
        break
      case '/authors':
        // 预加载热门诗人
        await this.dataManager.authors.getPopular(50)
        break
    }
  }
  
  // 2. 用户行为预测
  async predictAndPreload(userHistory: UserHistory) {
    // 基于浏览历史预测兴趣
    const interests = this.analyzeInterests(userHistory)
    
    // 预加载相关数据 (低优先级)
    if (interests.favoriteAuthors.length > 0) {
      requestIdleCallback(() => {
        interests.favoriteAuthors.forEach(author => {
          this.dataManager.authors.getByName(author)
        })
      })
    }
  }
  
  // 3. 空闲时预加载
  scheduleIdlePreloading() {
    requestIdleCallback(async (deadline) => {
      while (deadline.timeRemaining() > 0) {
        const nextChunk = this.getNextPriorityChunk()
        if (!nextChunk) break
        await this.loadChunk(nextChunk)
      }
    })
  }
}
```

### 6.3 缓存淘汰策略

```typescript
// LRU + 重要性加权淘汰

interface CacheItem<T> {
  data: T
  lastAccessed: number
  accessCount: number
  priority: number      // 用户标记的重要数据
  size: number          // 字节数
}

class WeightedLRUCache<T> {
  private cache = new Map<string, CacheItem<T>>()
  private maxSize: number
  private currentSize = 0
  
  // 计算淘汰分数 (越低越容易被淘汰)
  private getEvictionScore(item: CacheItem<T>): number {
    const age = Date.now() - item.lastAccessed
    const frequency = item.accessCount
    const priority = item.priority
    
    // 分数 = 年龄 / (频率 * 优先级)
    // 不常用的、旧的、低优先级的先被淘汰
    return age / (frequency * priority + 1)
  }
  
  evictIfNeeded(requiredSpace: number) {
    while (this.currentSize + requiredSpace > this.maxSize) {
      // 找到分数最低的项淘汰
      let lowestScore = Infinity
      let evictKey: string | null = null
      
      for (const [key, item] of this.cache) {
        const score = this.getEvictionScore(item)
        if (score < lowestScore) {
          lowestScore = score
          evictKey = key
        }
      }
      
      if (evictKey) {
        this.delete(evictKey)
      }
    }
  }
}
```

---

## 7. 搜索索引优化

### 7.1 多级搜索策略

```typescript
// 渐进式搜索，从快到慢

class SearchEngine {
  async search(query: SearchQuery): Promise<SearchResult> {
    const { keyword, filters, limit = 20 } = query
    
    // L1: 精确匹配 (内存索引，< 10ms)
    const exactMatches = this.memoryIndex.get(keyword)
    if (exactMatches && exactMatches.length >= limit) {
      return { results: exactMatches, source: 'memory' }
    }
    
    // L2: 前缀匹配 (IndexedDB 索引，< 50ms)
    const prefixMatches = await this.indexedDB.searchPrefix(keyword)
    if (prefixMatches.length >= limit) {
      return { results: prefixMatches, source: 'indexeddb' }
    }
    
    // L3: 全文搜索 (SQLite FTS5，< 100ms)
    const ftsResults = await this.sqlite.search(keyword)
    if (ftsResults.length > 0) {
      return { results: ftsResults, source: 'fts5' }
    }
    
    // L4: 模糊搜索 (FlexSearch，< 200ms)
    const fuzzyResults = await this.flexSearch.search(keyword, { fuzzy: 0.3 })
    if (fuzzyResults.length > 0) {
      return { results: fuzzyResults, source: 'fuzzy' }
    }
    
    // L5: 回退到扫描 (最慢，但总能返回结果)
    const scanResults = await this.fallbackScan(keyword, filters)
    return { results: scanResults, source: 'scan' }
  }
}
```

### 7.2 中文搜索优化

```typescript
// 针对中文的搜索优化

class ChineseSearchOptimizer {
  // 1. 分词索引
  tokenize(text: string): string[] {
    // 使用 jieba-wasm 或自定义词典分词
    // 同时保留单字索引支持单字搜索
    const words = jieba.cut(text)
    const chars = text.split('')
    return [...new Set([...words, ...chars])]
  }
  
  // 2. 拼音索引 (支持拼音搜索)
  buildPinyinIndex(text: string): string[] {
    const pinyin = pinyinPro.pinyin(text, { toneType: 'none' })
    const pinyinFirst = pinyinPro.pinyin(text, { 
      pattern: 'first',
      toneType: 'none' 
    })
    return [pinyin, pinyinFirst]
  }
  
  // 3. 同义词扩展
  expandSynonyms(keyword: string): string[] {
    const synonymMap = {
      '月亮': ['月', '明月', '皓月', '婵娟'],
      '离别': ['送别', '告别', '离愁', '相思'],
      // ...
    }
    return [keyword, ...(synonymMap[keyword] || [])]
  }
}
```

### 7.3 索引构建流程

```
构建流程 (构建时，非运行时):

原始数据
    │
    ▼
┌─────────────────┐
│ 1. 数据归一化    │  统一格式，去重
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 分词处理      │  标题、内容分词
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 倒排索引构建  │  词 → 文档ID列表
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌────────┐
│内存索引│  │SQLite  │  FTS5 表
│(JSON) │  │(WASM)  │
└───────┘  └────────┘
    │
    ▼
┌─────────────────┐
│ 4. 压缩打包      │  MessagePack + gzip
└────────┬────────┘
         │
         ▼
    部署到 CDN
```

---

## 8. 实施路线图

### 8.1 阶段规划

```
Phase 1: 基础设施 (1-2 周)
├── 统一 DataManager 实现
├── IndexedDB Schema 升级
└── 缓存淘汰策略实现

Phase 2: 搜索优化 (2-3 周)
├── 内存倒排索引构建
├── FlexSearch 集成
└── 多级搜索策略实现

Phase 3: 性能优化 (1-2 周)
├── Web Workers 数据解析
├── 智能预加载
└── 存储配额管理

Phase 4: 高级功能 (可选)
├── SQLite WASM 全文搜索
├── 拼音搜索支持
└── 语义搜索 (向量相似度)
```

### 8.2 关键代码结构

```
web/src/
├── stores/                      # Pinia 状态管理
│   ├── poemStore.ts
│   ├── authorStore.ts
│   └── searchStore.ts
│
├── data/                        # 数据管理层 (新)
│   ├── DataManager.ts           # 统一数据接口
│   ├── IndexManager.ts          # 搜索索引管理
│   ├── CacheManager.ts          # 缓存管理
│   └── adapters/
│       ├── IndexedDBAdapter.ts
│       ├── OPFSAdapter.ts
│       └── SQLiteAdapter.ts
│
├── search/                      # 搜索模块 (新)
│   ├── SearchEngine.ts
│   ├── InvertedIndex.ts
│   ├── ChineseTokenizer.ts
│   └── PinyinIndex.ts
│
├── workers/                     # Web Workers
│   ├── dataParser.worker.ts
│   └── indexBuilder.worker.ts
│
└── utils/
    ├── lruCache.ts
    ├── priorityQueue.ts
    └── compression.ts
```

### 8.3 预期收益

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 首屏搜索响应 | 2-5s | < 100ms | 20-50x |
| 诗词详情加载 | 500ms | < 50ms | 10x |
| 内存占用 | 无限制 | < 100MB | 可控 |
| 离线可用性 | 部分 | 完全 | 100% |

---

## 9. 总结

### 核心思路

1. **分层存储**: L1 内存 + L2 IndexedDB + L3 HTTP Cache，平衡速度与容量
2. **统一接口**: DataManager 提供一致的数据访问，隐藏底层复杂性
3. **智能索引**: 多级搜索策略，从内存索引到全文搜索渐进降级
4. **预加载**: 基于用户行为的智能预加载，提升感知性能
5. **中文优化**: 分词、拼音、同义词扩展，提升中文搜索体验

### 技术选型理由

- **保持 FlatBuffers**: 零拷贝解析优势，适合大数据量
- **引入 FlexSearch**: 客户端全文搜索的成熟方案
- **IndexedDB 为主**: 兼容性最好，容量足够
- **SQLite WASM 备选**: 未来可升级，支持更复杂查询

这个设计既解决了当前的搜索性能痛点，又为未来的功能扩展留下了空间。
