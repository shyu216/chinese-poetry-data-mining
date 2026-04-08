# 关键词详情页性能优化开发计划

## 背景与问题

### 问题描述
关键词详情页（`/keyword/:word`）加载缓慢，用户体感卡在转圈圈页面。

### 根本原因分析
1. **poem_index 数据缺少 chunk_id**：当前 poem_index 文件中每条记录只有 `id, title, author, dynasty, genre`，没有 `chunk_id` 字段
2. **keyword_index 数据缺少 chunk 信息**：关键词检索结果只返回 poem_id 数组，没有返回每首诗对应的 chunk 位置
3. **回退到 O(n) 扫描**：由于没有 chunk_id，加载时回退到逐个扫描所有 poem_index 分块，导致：
   - 加载 24 首诗词 = 24 × 28 = **672 次文件读取**
   - 每首诗调用 `getPoemById(poemId)` 走慢路径

### 日志证据
```
Step 1: Getting keyword poem IDs... ✅ (148 首诗词，约1200ms)
Step 2: Loading first page with 24 poems...
  -> Got 24 summaries from index in 372ms
  -> 0/24 poems have chunk_id  ← 关键问题
  -> Some poems missing chunk_id (0/24), falling back to individual loading
  -> Using slow path: scanning all chunks  ← 慢路径
```

---

## 解决方案

### 方案设计

#### 数据层打补丁（不重新生成数据）

**脚本1: `05_patch-poem-index-with-chunk-v2.cjs`**
- 目标：为 `results/poem_index/*.json` 注入 `chunk_id` 字段
- 输入：`results/preprocessed/poems_chunk_*.csv`（包含 poem_id -> chunk_id 映射）
- 输出：更新 `results/poem_index/poems_XX.json`，添加 `chunk_id` 字段
- 状态：**已有脚本，但未执行**（见 `scripts/05_patch-poem-index-with-chunk.cjs`）

**脚本2: `06_patch-keyword-index-with-chunk.cjs`（新增）**
- 目标：为 `results/keyword_index/*.json` 注入 chunk 信息
- 输入：
  - `results/keyword_index/keyword_XXXX.json`（关键词 -> poem_ids）
  - `results/poem_index/*.json`（已打补丁的 poem_index，含 chunk_id）
- 输出：更新 `results/keyword_index/keyword_XXXX.json`
  - 旧格式：`{ "明月": ["poem_id_1", "poem_id_2"] }`
  - 新格式：`{ "明月": [{ "id": "poem_id_1", "chunk_id": 5 }, { "id": "poem_id_2", "chunk_id": 12 }] }`

#### Web 端适配（不向下兼容）

**修改文件清单**

| 文件 | 修改内容 |
|------|----------|
| `web/src/composables/types.ts` | 新增 `KeywordPoemRef` 类型 |
| `web/src/composables/useSearchIndex.ts` | 修改 `getPoemSummariesByIds` 逻辑 |
| `web/src/composables/useKeywordIndex.ts` | 修改检索逻辑，直接返回含 chunk_id 的结果 |
| `web/src/views/KeywordDetailView.vue` | 移除 chunk_id 回退逻辑 |
| `web/src/views/AuthorDetailView.vue` | 同样受益于 chunk_id |

---

## 开发任务

### Phase 1: 数据补丁脚本

#### 任务1.1: 执行现有脚本
```bash
node scripts/05_patch-poem-index-with-chunk.cjs
```
- 验证 poem_index 是否已包含 chunk_id
- 如已执行，跳过

#### 任务1.2: 新增脚本 - keyword_index 打补丁
**文件**: `scripts/06_patch-keyword-index-with-chunk.cjs` ✅ **已创建**

**处理流程**:
1. 读取所有 `keyword_XXXX.json` 文件
2. 对每个关键词的 poem_ids：
   - 从已打补丁的 poem_index 中查询对应 chunk_id
   - 构建新格式：`[{ id, chunk_id }, ...]`
3. 写回文件（保持 JSON 格式化）
4. 更新 manifest 添加版本标记

**注意**: 
- 需要先确保 poem_index 已打补丁
- 预估处理时间：894 个文件，约 5-10 分钟

---

### Phase 2: Web 端适配

#### 任务2.1: 更新类型定义
**文件**: `web/src/composables/types.ts`

```typescript
// 新增类型
export interface KeywordPoemRef {
  id: string
  chunk_id: number
}

// PoemSummary 已有 chunk_id 字段（可选）
export interface PoemSummary {
  id: string
  title: string
  author: string
  dynasty: string
  genre: string
  chunk_id?: number  // 新增
}
```

#### 任务2.2: 修改 useKeywordIndex
**文件**: `web/src/composables/useKeywordIndex.ts`

修改 `getKeywordPoemIds` 方法：
- 旧逻辑：返回 `string[]`（只有 poem_id）
- 新逻辑：返回 `KeywordPoemRef[]`（含 id + chunk_id）

#### 任务2.3: 修改 KeywordDetailView
**文件**: `web/src/views/KeywordDetailView.vue`

```typescript
// 移除 chunk_id 缺失的 fallback 逻辑
// 旧代码：
if (idsWithChunkIds.length === batch.length) {
  // 优化路径
} else {
  // 回退到逐个加载 ← 删除
}

// 新代码：
// 直接使用 chunk_id 批量加载
const poemsWithDetails = await poems.getPoemsByIds(idsWithChunkIds, chunkIds)
```

#### 任务2.5: 修改 AuthorDetailView（可选，受益于此优化）
**文件**: `web/src/views/AuthorDetailView.vue`

同上，移除 fallback 逻辑

---

### Phase 3: 验证与测试

#### 验证清单
- [ ] 执行 `node scripts/05_patch-poem-index-with-chunk.cjs`（如需要）
- [ ] 执行 `node scripts/06_patch-keyword-index-with-chunk.cjs`
- [ ] 重启开发服务器 `npm run dev`
- [ ] 访问 `http://localhost:5173/keyword/明月照`
- [ ] 打开浏览器控制台，检查日志：
  - `0/24 poems have chunk_id` → 应该是 `24/24 poems have chunk_id`
  - `Using slow path` 日志不应再出现
- [ ] 确认页面加载时间显著缩短

---

## 时间线预估

| 任务 | 预估时间 |
|------|----------|
| Phase 1.1: 检查/执行 poem_index 补丁 | 5-10 分钟 |
| Phase 1.2: 开发 keyword_index 补丁脚本 | 30 分钟 |
| Phase 2.1-2.3: Web 端类型与 composable 修改 | 1 小时 |
| Phase 2.4-2.5: View 层修改 | 30 分钟 |
| Phase 3: 验证测试 | 30 分钟 |
| **总计** | **约 2.5-3 小时** |

---

## 风险与回滚

### 风险
1. **数据量**：keyword_index 有 894 个分片文件，处理时间较长
2. **存储空间**：新数据格式体积略增（约 10-20%）

### 回滚方案
- 保留原始 keyword_index 文件（备份）
- 如需回滚，删除补丁脚本输出的文件，恢复备份

---

## 依赖关系

```
Phase 1.1 (poem_index) → Phase 1.2 (keyword_index) → Phase 2 (Web)
        ↓                        ↓                        ↓
  数据准备阶段              数据补丁阶段            前端适配阶段
```

---

## 相关文件位置

### 脚本
- `scripts/05_patch-poem-index-with-chunk.cjs` - 现有脚本（待执行）
- `scripts/06_patch-keyword-index-with-chunk.cjs` - 新建

### Web 端
- `web/src/composables/types.ts` - 类型定义
- `web/src/composables/useKeywordIndex.ts` - 关键词索引
- `web/src/composables/useSearchIndex.ts` - 搜索索引
- `web/src/views/KeywordDetailView.vue` - 关键词详情页
- `web/src/views/AuthorDetailView.vue` - 作者详情页

### 数据
- `results/poem_index/` - 诗词索引
- `results/keyword_index/` - 关键词索引
- `results/preprocessed/` - 原始分块数据

---

*文档创建时间: 2026-04-08*
*最后更新时间: 2026-04-08*
