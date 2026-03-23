# Hash 验证缓存迁移开发计划

**日期**: 2026-03-22  
**目标**: 将所有数据加载逻辑迁移到带 hash 验证的缓存系统  
**背景**: 已实现 `useVerifiedCache.ts` 和 `generate-hash-manifest.js`，需要全面迁移现有代码
**状态**: ✅ **全部完成**

---

## 已完成的基础工作

1. ✅ `scripts/generate-hash-manifest.js` - 构建时生成文件 hash 清单
2. ✅ `src/composables/useCacheV2.ts` - 扩展支持 hash 字段
3. ✅ `src/composables/useVerifiedCache.ts` - 带验证的缓存组合式函数
4. ✅ `.github/workflows/deploy-pages.yml` - CI/CD 集成 hash 生成

---

## 迁移任务清单

### Phase 1: 核心数据模块 (高优先级) ✅ 完成

#### 1.1 usePoemsV2.ts ✅
- **文件**: `src/composables/usePoemsV2.ts`
- **涉及接口**: 
  - `loadChunkSummaries(chunkNum)` → `getVerifiedChunk()`
- **数据文件**: 
  - `data/preprocessed/poems_chunk_${chunkId}.csv` (0000-0255)
- **存储键**: `POEMS_SUMMARY_STORAGE`
- **状态**: ✅ 已完成

#### 1.2 useAuthorsV2.ts ✅
- **文件**: `src/composables/useAuthorsV2.ts`
- **涉及接口**:
  - `loadAuthorChunk(chunkId)` → `getVerifiedChunk()`
- **数据文件**:
  - `data/author_v2/author_chunk_${chunkIdStr}.fbs` (0000-0045)
- **存储键**: `AUTHORS_STORAGE`
- **状态**: ✅ 已完成

### Phase 2: 搜索索引模块 (中优先级) ✅ 完成

#### 2.1 useSearchIndexV2.ts ✅
- **文件**: `src/composables/useSearchIndexV2.ts`
- **涉及接口**:
  - `loadPoemChunk(prefix)` → `getVerifiedChunk()`
- **数据文件**:
  - `data/poem_index/${fileName}` (大量文件)
- **存储键**: `POEM_INDEX_STORAGE`
- **状态**: ✅ 已完成

#### 2.2 useKeywordIndex.ts ✅
- **文件**: `src/composables/useKeywordIndex.ts`
- **涉及接口**:
  - `loadMetadata()` → `getVerifiedCache()`
  - `loadChunk(chunkIndex)` → `getVerifiedChunk()`
- **数据文件**:
  - `data/keyword_index/metadata.json`
  - `data/keyword_index/keyword_${chunkId}.json`
- **存储键**: `KEYWORD_INDEX_STORAGE`
- **状态**: ✅ 已完成

### Phase 3: 词相似度与词频 (中优先级) ✅ 完成

#### 3.1 useWordSimilarityV2.ts ✅
- **文件**: `src/composables/useWordSimilarityV2.ts`
- **涉及接口**:
  - `loadVocab()` → `getVerifiedCache()`
  - `loadChunk(chunkId)` → `getVerifiedChunk()`
- **数据文件**:
  - `data/word_similarity_v3/vocab.json`
  - `data/word_similarity_v3/word_chunk_${chunkIdStr}.bin`
- **存储键**: `WORD_SIMILARITY_STORAGE`
- **状态**: ✅ 已完成

#### 3.2 useWordcountV2.ts ✅
- **文件**: `src/composables/useWordcountV2.ts`
- **涉及接口**:
  - `loadChunk(chunkIndex)` → `getVerifiedChunk()`
- **数据文件**:
  - `data/wordcount_v2/chunk_${chunkId}.json`
- **存储键**: `WORDCOUNT_STORAGE`
- **状态**: ✅ 已完成

### Phase 4: 元数据加载器 (中优先级) ✅ 完成

#### 4.1 useMetadataLoader.ts ✅
- **文件**: `src/composables/useMetadataLoader.ts`
- **涉及接口**:
  - `useMetadataLoader()` 中的 `loadMetadata()` → `getVerifiedCache()`
- **数据文件**:
  - `data/author_v2/authors-meta.json`
  - `data/preprocessed/poems_chunk_meta.json`
  - `data/wordcount_v2/meta.json`
  - `data/word_similarity_v3/metadata.json`
  - `data/poem_index/poem_index_manifest.json`
- **状态**: ✅ 已完成

---

## 迁移完成总结

### 已迁移文件清单

| 文件 | 模块类型 | 状态 |
|------|----------|------|
| `src/composables/usePoemsV2.ts` | 核心数据 | ✅ |
| `src/composables/useAuthorsV2.ts` | 核心数据 | ✅ |
| `src/composables/useSearchIndexV2.ts` | 搜索索引 | ✅ |
| `src/composables/useKeywordIndex.ts` | 搜索索引 | ✅ |
| `src/composables/useWordSimilarityV2.ts` | 词相似度 | ✅ |
| `src/composables/useWordcountV2.ts` | 词频统计 | ✅ |
| `src/composables/useMetadataLoader.ts` | 元数据 | ✅ |
| `src/search/SearchManager.ts` | 搜索管理 | ✅ |
| `src/composables/useAuthorClusters.ts` | 聚类数据 | ✅ |
| `src/utils/wordSimilarityLoader.ts` | 工具类 | ✅ |

### 迁移模式模板

#### 模式 A: 分块数据迁移 (如 poems_chunk_*.csv)

```typescript
// 迁移后
const result = await getVerifiedChunk<PoemSummary[]>(
  POEMS_SUMMARY_STORAGE,
  chunkNum,
  `preprocessed/poems_chunk_${chunkId}.csv`, // manifest 中的相对路径
  async () => {
    const response = await fetch(`${import.meta.env.BASE_URL}data/preprocessed/poems_chunk_${chunkId}.csv`)
    if (!response.ok) throw new Error(`Failed to load chunk ${chunkNum}`)
    const csvText = await response.text()
    // ... 解析逻辑
    return poems
  }
)

if (result.data) {
  poemSummaryCache.value.set(chunkNum, result.data)
  return result.data
}
```

#### 模式 B: 元数据迁移 (如 authors-meta.json)

```typescript
// 迁移后
const result = await getVerifiedCache<T>(
  config.storageName,
  'metadata',
  config.url.replace('/data/', ''), // 转换为相对路径
  async () => {
    const response = await fetch(`${import.meta.env.BASE_URL}${config.url}`)
    if (!response.ok) throw new Error('Failed to load metadata')
    return response.json()
  }
)

return result.data
```

---

## 后续工作建议

1. **测试验证**: 运行完整测试确保所有模块正常工作
2. **性能监控**: 监控首次加载和缓存命中率
3. **清理旧代码**: 移除未使用的 `getChunkedCache` / `setChunkedCache` 调用
4. **文档更新**: 更新开发者文档说明新的缓存使用方式

---

## 测试策略

1. **单元测试**: 每个迁移后的模块单独测试
2. **集成测试**: 确保模块间协作正常
3. **性能测试**: 验证缓存命中率提升
4. **回归测试**: 确保功能无损

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| CSV/二进制解析错误 | 高 | 保持原有解析逻辑不变，仅包装 loader |
| Hash 不匹配导致频繁刷新 | 中 | 检查 manifest 生成是否正确 |
| 内存占用增加 | 低 | 保持原有的 shallowRef 缓存策略 |
| 首次加载变慢 | 低 | manifest 文件很小，影响可忽略 |

---

## 成功标准

- [ ] 所有数据加载都通过 `useVerifiedCache`
- [ ] 构建时自动生成 hash-manifest.json
- [ ] 文件更新后缓存自动失效
- [ ] 控制台显示 `[VerifiedCache] Hit/Miss` 日志
- [ ] 无功能回归
- [ ] 性能持平或提升
