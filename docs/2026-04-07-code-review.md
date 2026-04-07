# 2026-04-07 代码现状分析

## 概览

当前前端有 **4 种核心数据**，分别走不同的加载管道。

---

## 一、Poems（诗词）

### 数据来源

```
data/preprocessed/poems_chunk_XXXX.csv   # 摘要（CSV）
data/poem_index/poem_index_XXXX.json      # 详情/索引（JSON）
```

### 数据类型

| 类型 | 结构 | 用途 |
|------|------|------|
| PoemSummary | id, title, author, dynasty, genre | 列表展示 |
| PoemDetail | 摘要 + 原文、译文、注释 | 详情页 |
| PoemIndex | id -> PoemSummary 映射 | 搜索 |

### 加载管道

```
usePoemsV2
  ├── loadMetadata()                    # 拉 poems_chunk_meta.json
  │                                      # → total, chunks, stats
  │
  ├── loadChunkSummaries(chunkId)       # 按需拉 CSV
  │   ├── getVerifiedChunk()            # Hash 验证
  │   ├── fetch data/poems_chunk_XXXX.csv
  │   ├── parseCsvLine()                # 逐行解析
  │   └── 存 IndexedDB + 内存
  │
  └── getPoemDetail(id)                 # 详情页用
      ├── 查内存 cache → 有就返回
      └── 无 → fetch JSON → 存 IndexedDB
```

### 关键函数

```typescript
// composables/usePoemsV2.ts
loadMetadata(forceRefresh?: boolean)      // 加载元数据
loadChunkSummaries(chunkId: number)      // 加载摘要分片
getPoemDetail(id: string)                // 加载详情
queryPoems(filter, options)               // 按条件查询
```

---

## 二、Authors（作者）

### 数据来源

```
data/author_v2/authors-meta.json         # 元数据
data/author_v2/author_chunk_XXXX.bin     # FlatBuffers 二进制
```

### 数据类型

| 类型 | 结构 | 用途 |
|------|------|------|
| AuthorStats | name, dynasty, poems_count, word_frequency, similar_authors | 作者详情 |
| AuthorsIndex | total, chunks, stats | 列表页统计 |

### 加载管道

```
useAuthorsV2
  ├── loadMetadata()                     # 拉 authors-meta.json
  │
  └── loadChunk(chunkId)                 # 拉 FlatBuffers
      ├── getVerifiedChunk()
      ├── fetch author_chunk_XXXX.bin
      ├── flatbuffers 解析
      │   ├── Author → AuthorStats
      │   ├── WordFreq → word_frequency
      │   ├── MeterPattern → meter_patterns
      │   └── SimilarAuthor → similar_authors
      └── 存内存
```

### 关键函数

```typescript
// composables/useAuthorsV2.ts
loadMetadata(forceRefresh?)              // 元数据
loadChunk(chunkId)                       // 加载单个分片
getAuthorById(id)                        // 按 ID 查
getAuthorsByChunk(chunkId)              // 按分片查
```

### 特点

- **FlatBuffers 二进制**：比 JSON 小，解析快
- **无摘要/详情分离**：一次性加载整个 AuthorStats

---

## 三、WordCount（词频）

### 数据来源

```
data/wordcount_v2/meta.json              # 元数据
data/wordcount_v2/chunk_XXXX.json        # 分片 JSON
```

### 数据类型

| 类型 | 结构 | 用途 |
|------|------|------|
| WordCountItem | word, count, rank | 词频统计 |
| WordCountMeta | total_words, total_chunks | 列表页 |

### 加载管道

```
useWordcountV2
  ├── loadMetadata()                     # 拉 meta.json
  │
  └── loadChunk(chunkId)                 # 拉 JSON 分片
      ├── getVerifiedChunk()
      ├── fetch chunk_XXXX.json
      ├── [[word, count, rank], ...]    # 原始格式
      └── 转换为 WordCountItem[]
```

### 关键函数

```typescript
// composables/useWordcountV2.ts
loadMetadata(forceRefresh?)
loadChunk(chunkId)
getWordCounts(startRank, endRank)       # 按排名区间
getTopWords(n)                          # Top N
```

---

## 四、WordSimilarity（词相似度）

### 数据来源

```
data/word_similarity_v3/metadata.json   # 元数据
data/word_similarity_v3/*.bin           # FlatBuffers 词向量
```

### 数据类型

| 类型 | 结构 | 用途 |
|------|------|------|
| SimilarWordResult | word, similarity | 相似词推荐 |
| WordSimilarityMetadata | vocab_size, chunks | 元数据 |

### 加载管道

```
useWordSimilarityV2
  ├── loadMetadata()                     # 拉 metadata.json
  │                                      # → vocab 映射
  ├── computeVocabHash()                 # 验证缓存一致性
  │
  └── loadChunk(chunkId)                 # 拉 FlatBuffers
      ├── getVerifiedChunk()
      ├── fetch word_similarity_XXXX.bin
      ├── flatbuffers 解析
      │   ├── vocab[]                    # 词表
      │   └── entries                    # 相似词数据
      ├── 构建 Map<wordId, similarWords>
      └── 存内存
```

### 关键函数

```typescript
// composables/useWordSimilarityV2.ts
loadMetadata(forceRefresh?)
loadChunk(chunkId)
findSimilarWords(word, topK)             # 找相似词
getVocabulary()                          # 全部词汇
```

### 特点

- **最复杂**：词向量数据大，FlatBuffers + 哈希验证
- **无分页**：一次性加载 vocab 到内存

---

## 五、Search（搜索）

### 数据来源

```
data/poem_index/poem_index_manifest.json  # 索引 manifest
data/poem_index/poem_index_XXXX.json       # 倒排索引
data/keyword_index/keyword_XXXX.json       # 关键词索引
```

### 加载管道

```
useSearchIndexV2
  ├── loadMetadata()                      # 拉 manifest
  │                                       # → prefix -> filename 映射
  │
  └── loadPoemChunk(prefix)              # 按前缀加载
      ├── getVerifiedChunk()
      ├── fetch poem_index_XXXX.json
      ├── { id: PoemSummary, ... }       # ID → 摘要映射
      └── 存 Map<string, PoemSummary>

useKeywordIndex
  ├── loadManifest()                     # 拉 keyword_manifest.json
  │                                      # → keyword → chunkId
  └── loadChunk(chunkId)                 # 拉倒排索引
      ├── 关键词 → [poemId, ...]
      └── 存内存
```

### 关键函数

```typescript
// composables/useSearchIndexV2.ts
loadPoemChunk(prefix)                    # 加载索引分片
searchPoemById(id)                       # 按 ID 查
searchByKeyword(keyword)                 # 关键词搜索
searchPoems(filters, options)            # 组合搜索

// composables/useKeywordIndex.ts
loadManifest()                            # 加载关键词 manifest
searchByKeyword(keyword)                 # 关键词搜索
```

---

## 六、缓存架构

### 三层缓存

```
┌─────────────────────────────────────────┐
│  1. 内存缓存 (Map / shallowRef)          │
│     - 最快，进程级，重启丢失              │
└─────────────────────────────────────────┘
                    ↓ Miss
┌─────────────────────────────────────────┐
│  2. IndexedDB (idb 库)                  │
│     - 持久化，跨会话                     │
│     - 有版本验证 (hash / version)        │
└─────────────────────────────────────────┘
                    ↓ Miss
┌─────────────────────────────────────────┐
│  3. 网络 (fetch)                        │
│     - 从 CDN / 静态文件拉                │
└─────────────────────────────────────────┘
```

### 验证机制

```typescript
// useVerifiedCache.ts
getVerifiedChunk()
  ├── 检查 IndexedDB 有无有效缓存
  │   ├── 有 → 验证 hash / version
  │   │   ├── 有效 → 返回缓存
  │   │   └── 无效 → 重新 fetch
  └── 无 → 重新 fetch
```

### Metadata 存储

```typescript
// IndexedDB metadata 表
{
  storage: 'poems-index',     // 存储名
  loadedChunkIds: [0,1,2],    // 已加载的分片
  totalChunks: 10,            // 总分片
  version: 1,                 // 版本号
  dependencyHash: '...'       // 依赖哈希
}
```

---

## 七、现有问题

| 问题 | 位置 | 影响 |
|------|------|------|
| CSV 解析在主线程 | usePoemsV2 | 大分片卡顿 |
| FlatBuffers 解析在主线程 | useAuthorsV2, useWordSimilarityV2 | 同上 |
| 无统一错误处理 | 各 composable | 用户体验差 |
| 首页并行加载过多 | HomeView | 首屏慢 |
| 无骨架屏 | views/ | 加载时白屏 |
| 无增量更新 | 所有 | 版本更新需全量刷新 |

---

## 八、数据流全景图

```
                    ┌──────────────────────────────────────┐
                    │           HomeView.vue              │
                    │  (首页，触发所有 metadata 加载)     │
                    └──────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   usePoemsV2         │  │   useAuthorsV2       │  │ useWordSimilarityV2  │
│   - loadMetadata     │  │   - loadMetadata     │  │ - loadMetadata       │
│   - loadChunk*       │  │   - loadChunk        │  │ - loadChunk          │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │         useMetadataLoader             │
                    │  (统一元数据加载入口)                 │
                    └──────────────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
         ┌─────────────────────┐              ┌─────────────────────┐
         │   useVerifiedCache  │              │    useCacheV2        │
         │ (Hash 版本验证)      │              │  (IndexedDB 封装)    │
         └─────────────────────┘              └─────────────────────┘
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   IndexedDB     │
                              │   (持久化缓存)   │
                              └─────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   fetch / CDN   │
                              │  (静态数据文件)  │
                              └─────────────────┘
```

---

## 九、Views 与数据对应

| View | 主要 Composable | 数据 |
|------|-----------------|------|
| HomeView | usePoemsV2, useAuthorsV2, useWordSimilarityV2 | 统计 + 随机诗 |
| PoemsView | usePoemsV2, useChunkLoader | 诗词列表 |
| PoemDetailView | usePoemsV2 | 诗词详情 |
| AuthorsView | useAuthorsV2 | 作者列表 |
| AuthorDetailView | useAuthorsV2 | 作者详情 |
| WordCountView | useWordcountV2 | 词频统计 |
| KeywordDetailView | useKeywordIndex, useWordSimilarityV2 | 关键词分析 |
| ClusterDetailView | useAuthorClusters | 聚类可视化 |

---

## 十、结论

现有架构**已经有很好的基础**：

- 分层缓存（内存 → IndexedDB → 网络）
- 版本验证（hash / version）
- 按需加载（chunk 分片）
- 类型安全（TypeScript）

**但需要优化**：

1. **主线程阻塞**：CSV / FlatBuffers 解析 → 用 Web Worker
2. **首屏体验**：骨架屏 + 关键数据预加载
3. **增量更新**：每次只下变化的部分
4. **错误处理**：统一的 fallback 和重试
5. **代码复用**：提炼通用模式（现在每個composable重复类似逻辑）
