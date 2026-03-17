# 统一数据管理系统设计文档

> 日期: 2026-03-17
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
| useKeywordIndex | JSON (.json) | **仅内存，无持久化** | **无** | 关键词索引 |

### 1.2 完整数据流分析

#### 1. 诗词 (Poems) - usePoemsV2
```
数据源: data/preprocessed/poems_chunk_*.csv
  ↓ fetch CSV
  ↓ parseCsvLine() 解析
  ↓ setChunkedCache() 存入 IndexedDB
存储: poems-summary-v2 / poems-detail-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 2. 诗人 (Authors) - useAuthorsV2
```
数据源: data/author_v2/author_chunk_*.fbs
  ↓ fetch FBS
  ↓ flatbuffers 解析
  ↓ setChunkedCache() 存入 IndexedDB
存储: authors-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 3. 词频 (WordCount) - useWordcountV2
```
数据源: data/wordcount_v2/chunk_*.json
  ↓ fetch JSON
  ↓ setChunkedCache() 存入 IndexedDB
存储: wordcount-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 4. 词境 (WordSimilarity) - useWordSimilarityV2
```
数据源: data/word_similarity_v3/word_chunk_*.bin
  ↓ fetch FBS
  ↓ parseWordSimilarityChunk() 解析
  ↓ setChunkedCache() 存入 IndexedDB
存储: word-similarity-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON ⚠️ 问题：可能缓存失效
```

#### 5. 诗词索引 (PoemIndex) - useSearchIndexV2
```
数据源: data/poem_index/poems_*.json
  ↓ fetch JSON
  ↓ setChunkedCache() 存入 IndexedDB
存储: poem-index-v2 (JSON)
缓存: getChunkedCache() → 直接返回 JSON
```

#### 6. 关键词索引 (KeywordIndex) - useKeywordIndex ⚠️ 特殊
```
数据源: results/keyword_index/keyword_*.json
  ↓ fetch JSON
  ↓ 仅存入内存 Map (keywordCache)
  ↓ localStorage 仅存 metadata
存储: 无 IndexedDB!
缓存: 无持久化缓存，刷新后需重新加载
```

### 1.3 数据文件位置

| 数据类型 | 目录 | 文件模式 |
|---------|------|---------|
| 诗词 | data/preprocessed/ | poems_chunk_*.csv |
| 诗人 | data/author_v2/ | author_chunk_*.fbs |
| 词频 | data/wordcount_v2/ | chunk_*.json |
| 词境 | data/word_similarity_v3/ | word_chunk_*.bin |
| 诗词索引 | data/poem_index/ | poems_*.json |
| 关键词索引 | results/keyword_index/ | keyword_*.json |

### 1.4 当前问题

**核心问题：IndexedDB 缓存是否有效？**

理论上：
```
首次访问: 下载 → 解析 → 存入 IndexedDB
二次访问: getChunkedCache → 直接返回 JSON (无需解析!)
```

但实际上用户反馈 FBS 仍然每次都解析，可能原因：
1. 浏览器存储空间不足，IndexedDB 缓存被清除
2. 用户首次访问
3. 缓存 key 不匹配（storage name 或 chunkId 不一致）
4. 缓存数据损坏

其他问题：
1. **存储状态不透明**: 无法看到 IndexedDB 里存的是什么格式
2. **手动触发困难**: 无法手动触发"重新下载并转换"
3. **无法区分来源**: 不知道当前数据是从网络还是缓存来的
4. **关键词索引无持久化**: useKeywordIndex 没有使用 IndexedDB，仅存内存

---

## 2. WordSim 使用分析

### 2.1 数据流程

```
WordSimView.vue:
  → useWordSimilarityV2.loadVocab()     // 加载词表
  → useWordSimilarityV2.loadChunk(id)   // 加载具体 chunk

loadChunk 逻辑 (useWordSimilarityV2.ts):
  1. 检查内存缓存: chunkCache (Map)
  2. 检查 IndexedDB: getChunkedCache(storage, chunkId)
  3. 如果没有: fetch .bin → parse FBS → setChunkedCache → 返回
```

### 2.2 存储结构

IndexedDB 中有两个表：
- `cache`: 存储 chunk 数据 (key = `word-similarity-v2:chunk:${chunkId}`)
- `metadata`: 存储元数据 (key = `word-similarity-v2`)

vocab 存储位置：`cache` 表，key = `word-similarity-v2:vocab`

### 2.3 发现的问题

**Bug: DataStorage 和 DataOverview 中的查询错误**

```typescript
// ❌ 错误用法 - 查的是 metadata 表
const wordSimVocab = await getMetadata(WORD_SIMILARITY_STORAGE)

// ✅ 正确用法 - 应该查 cache 表
const wordSimVocab = await getCache(WORD_SIMILARITY_STORAGE, 'vocab')
```

这会导致误判 vocab 是否已缓存！

### 2.4 目标需求

根据用户需求：
1. **可跳转**: wordSim, wordcount 能相互跳转
2. **可视化**: Data 中能正确显示 IndexedDB 中 wordSim 的 chunk 情况
3. **统一处理**: 统一管理不同任务的数据
4. **高性能**: 不卡顿，不耗尽资源
5. **容错性**: 包容用户不同行为

---

## 3. 设计原则

### 2.1 核心原则

1. **透明转换**: 用户无感知地从 FBS 转换到 JSON
2. **按需加载**: 只加载需要的数据 chunk
3. **统一接口**: 所有数据类型使用相同的 API
4. **可观测性**: 完整的状态监控和日志
5. **容错性**: 包容用户的各种操作行为

### 2.2 性能原则

1. **首次优化**: 首次访问后，后续访问应 < 50ms
2. **内存约束**: 单个 chunk 最大 1MB，总内存 < 100MB
3. **懒解析**: 只在需要时解析 FBS
4. **增量存储**: 分批写入 IndexedDB，避免卡顿

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      UI Layer                                │
│  (DataDashboard, WordSimView, WordCountView, etc.)          │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   Unified Data Manager                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              DataManager (单例)                      │    │
│  │  - registerDataType()                               │    │
│  │  - loadChunk()                                      │    │
│  │  - getStats()                                       │    │
│  │  - convertFormat()                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Network     │   │  Memory Cache   │   │   IndexedDB     │
│  (原始数据)   │   │  (热数据)        │   │   (持久化)       │
│  - .bin (FBS)│   │  - Map<key, data>   │   │   - JSON chunks│
│  - .json     │   │  - LRU 策略        │   │   - metadata   │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

### 3.2 数据流

```
首次访问:
  Network (FBS) → 解析 → 内存 → IndexedDB (JSON) → 后续直接读取

二次访问:
  IndexedDB (JSON) → 内存 → UI
```

---

## 4. 核心接口设计

### 4.1 DataTypeConfig - 数据类型配置

```typescript
interface DataTypeConfig<T = any> {
  // 唯一标识
  type: string  // 'poems' | 'authors' | 'wordcount' | 'wordSimilarity' | 'poemIndex'
  
  // 存储配置
  storage: string  // IndexedDB storage name
  
  // 数据源
  sources: {
    // 原始数据源 (FBS)
    raw?: {
      urlPattern: string  // e.g., 'data/word_similarity_v3/word_chunk_{id}.bin'
      parser: (buffer: Uint8Array) => Promise<ParsedData>
    }
    // 预处理数据源 (JSON)
    processed?: {
      urlPattern: string  // e.g., 'data/word_similarity_v3/word_chunk_{id}.json'
      parser: (data: any) => ParsedData
    }
  }
  
  // metadata 配置
  metadata: {
    url: string
    parser: (data: any) => Metadata
  }
  
  // 缓存配置
  cache: {
    maxMemoryItems: number      // 内存缓存最大数量
    maxMemorySize: number       // 内存缓存最大字节
    chunkSize: number           // 单个 chunk 大小
  }
  
  // 转换配置
  conversion?: {
    enabled: boolean           // 是否支持格式转换
    targetFormat: 'json'       // 转换目标格式
    transform: (raw: ParsedData) => TransformedData  // 转换函数
  }
}
```

### 4.2 DataManager - 统一数据管理器

```typescript
class DataManager {
  // 注册数据类型
  registerType<T>(config: DataTypeConfig<T>): void
  
  // 加载单个 chunk
  async loadChunk(type: string, chunkId: number): Promise<ChunkData>
  
  // 批量加载 chunks
  async loadChunks(type: string, chunkIds: number[]): Promise<ChunkData[]>
  
  // 获取数据状态
  async getStats(type: string): Promise<DataStats>
  
  // 获取所有数据类型状态
  async getAllStats(): Promise<Record<string, DataStats>>
  
  // 清除缓存
  async clearCache(type?: string): Promise<void>
  
  // 转换格式 (FBS → JSON)
  async convertFormat(type: string): Promise<ConversionResult>
  
  // 监听状态变化
  subscribe(type: string, callback: (stats: DataStats) => void): Unsubscribe
}
```

### 4.3 数据状态

```typescript
interface DataStats {
  type: string
  
  // 原始数据 (FBS)
  raw: {
    totalChunks: number
    cachedChunks: number
    size: number
  }
  
  // 预处理数据 (JSON)
  processed: {
    totalChunks: number
    cachedChunks: number
    size: number
  }
  
  // 内存缓存
  memory: {
    cachedChunks: number
    size: number
  }
  
  // 状态
  status: 'idle' | 'loading' | 'converting' | 'error'
  lastUpdated: number
  error?: string
}
```

---

## 5. 存储策略

### 5.1 IndexedDB Schema

```typescript
// 统一存储 schema
interface UnifiedSchema {
  // 元数据
  'metadata': {
    key: string  // data type
    value: {
      type: string
      loadedRawChunkIds: number[]
      loadedProcessedChunkIds: number[]
      conversionStatus: 'none' | 'converting' | 'completed'
      lastUpdated: number
    }
  }
  
  // 原始数据 (FBS 解析后, 可能是中间格式)
  'raw': {
    key: string  // `${type}:${chunkId}`
    value: {
      type: string
      chunkId: number
      data: any  // 解析后的对象
      timestamp: number
    }
  }
  
  // 预处理数据 (JSON)
  'processed': {
    key: string  // `${type}:${chunkId}`
    value: {
      type: string
      chunkId: number
      data: any
      size: number
      timestamp: number
    }
  }
  
  // 词汇表 (大数据量)
  'vocab': {
    key: string  // type
    value: {
      type: string
      map: Record<string, number>  // word → id
      reverseMap: Record<number, string>  // id → word
      size: number
    }
  }
}
```

### 5.2 存储优先级

1. **metadata**: 必须存储，用于状态追踪
2. **vocab**: 大词汇量，优先存储
3. **processed (JSON)**: 访问快，优先存储
4. **raw (解析后)**: 可选，内存压力大时释放

---

## 6. 转换策略 (FBS → JSON)

### 6.1 转换触发条件

```typescript
// 自动转换策略
const conversionPolicy = {
  // 1. 用户手动触发
  manual: true,
  
  // 2. 首次访问自动转换
  autoOnFirstAccess: true,
  
  // 3. 空闲时后台转换
  backgroundOnIdle: true,
  
  // 4. 转换阈值
  threshold: {
    maxChunkSizeForAuto: 1024 * 1024,  // 1MB
    idleTimeMs: 5000  // 5秒空闲
  }
}
```

### 6.2 转换流程

```
1. 检测: chunk 是否需要转换?
   ↓
2. 解析: 使用 flatbuffers 解析 .bin 文件
   ↓
3. 转换: 转换为优化的 JSON 格式
   ↓
4. 存储: 分批写入 IndexedDB (每批 50 条)
   ↓
5. 更新: 更新 metadata 状态
   ↓
6. 清理: 删除原始解析数据 (可选)
```

### 6.3 转换优化

- **分批写入**: 每批 50 个 chunk，避免阻塞
- **后台执行**: 使用 requestIdleCallback
- **进度追踪**: 实时更新转换进度
- **中断恢复**: 支持中断后继续

---

## 7. 监控与可观测性

### 7.1 性能指标

```typescript
interface PerformanceMetrics {
  // 加载时间
  loadTime: {
    network: number      // 网络下载时间
    parse: number       // 解析时间
    transform: number   // 转换时间
    storage: number      // 存储时间
    total: number       // 总时间
  }
  
  // 缓存命中率
  cacheHitRate: {
    memory: number      // 内存缓存命中率
    indexedDB: number   // IndexedDB 命中率
  }
  
  // 资源使用
  resources: {
    memoryUsed: number   // 当前内存使用
    storageUsed: number  // IndexedDB 使用
    chunksLoaded: number // 已加载 chunks
  }
}
```

### 7.2 日志系统

```typescript
// 日志级别
enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

// 统一日志接口
function log(level: LogLevel, category: string, message: string, data?: any): void

// 关键日志点
const LOG_CATEGORIES = {
  LOAD_CHUNK: 'data:load:chunk',
  CONVERT: 'data:convert',
  CACHE_HIT: 'data:cache:hit',
  CACHE_MISS: 'data:cache:miss',
  STORAGE: 'data:storage',
  ERROR: 'data:error'
}
```

---

## 8. DataDashboard 增强

### 8.1 展示信息

```typescript
interface DashboardDisplay {
  // 每个数据类型的详细状态
  types: {
    [type: string]: {
      // 基本信息
      name: string           // 显示名称
      description: string   // 描述
      
      // 存储状态
      storage: {
        raw: {
          totalChunks: number
          cachedChunks: number
          size: string        // 格式化后
          status: 'none' | 'partial' | 'complete'
        }
        processed: {
          totalChunks: number
          cachedChunks: number
          size: string
          status: 'none' | 'converting' | 'partial' | 'complete'
        }
      }
      
      // 操作
      actions: {
        canConvert: boolean       // 可转换为 JSON
        canClear: boolean         // 可清除
        canReload: boolean        // 可重新加载
      }
      
      // 进度
      progress?: {
        converting: number        // 0-100
        loading: number            // 0-100
      }
    }
  }
  
  // 总体统计
  total: {
    storageUsed: string
    chunksLoaded: number
    conversionProgress: number
  }
}
```

### 8.2 用户操作

1. **查看状态**: 一目了然看到每个数据的存储情况
2. **手动转换**: 一键将 FBS 转换为 JSON
3. **清除缓存**: 选择性清除特定数据
4. **重新加载**: 强制重新从网络加载

---

## 9. 实施计划

### Phase 1: 基础设施 (1天)

- [ ] 重构 `useCacheV2`，支持多格式存储
- [ ] 实现 `DataManager` 核心类
- [ ] 定义 `DataTypeConfig` 接口

### Phase 2: WordSim 迁移 (2天)

- [ ] 为 WordSim 注册数据类型
- [ ] 实现 FBS → JSON 转换逻辑
- [ ] 集成到 `useWordSimilarityV2`
- [ ] 更新 DataDashboard 显示

### Phase 3: 其他数据类型 (2天)

- [ ] 迁移 WordCount
- [ ] 迁移 Authors
- [ ] 迁移 Poems

### Phase 4: 优化与增强 (1天)

- [ ] 实现 LRU 内存缓存
- [ ] 后台转换优化
- [ ] 完整监控面板

---

## 10. 附录

### A. 相关文件位置

```
web/src/
├── composables/
│   ├── useCacheV2.ts          # 现有缓存层
│   ├── useMetadataLoader.ts   # 元数据加载
│   ├── useWordSimilarityV2.ts # WordSim 业务逻辑
│   └── useWordcountV2.ts      # WordCount 业务逻辑
├── components/
│   └── data/
│       ├── DataDashboardView.vue
│       ├── DataOverview.vue
│       ├── DataDownload.vue
│       └── DataStorage.vue
└── views/
    └── WordSimView.vue        # WordSim 页面
```

### B. 关键依赖

- `flatbuffers`: FBS 解析
- `idb`: IndexedDB 封装
- `naive-ui`: UI 组件

### C. 性能基准

| 操作 | 当前 | 目标 |
|------|------|------|
| 首次加载 WordSim chunk | 500-2000ms | 500-2000ms |
| 二次加载 WordSim chunk | 500-2000ms | < 50ms |
| DataDashboard 加载 | 500ms | < 200ms |
| 内存占用 (20万词) | ~200MB | < 100MB |
