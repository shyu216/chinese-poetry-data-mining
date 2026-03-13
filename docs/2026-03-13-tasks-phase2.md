# 任务分配 - Phase 2 (静态部署优化版) - 2026-03-13

**项目**: chinese-poetry-data-mining  
**分支**: refactor/pipeline-v2  
**状态**: 待分配  
**部署方式**: 纯静态部署 (GitHub Pages)

---

## 关键约束：纯静态部署

由于项目使用 GitHub Pages 进行纯静态部署，**所有功能必须满足以下约束**：

| 约束 | 说明 | 解决方案 |
|------|------|----------|
| ❌ 无后端服务 | 无法运行 Flask/Django 等后端 | 所有计算在构建时完成，前端仅做查询 |
| ❌ 无实时计算 | 无法执行相似度计算等复杂运算 | 预计算所有结果，生成静态索引文件 |
| ❌ 无数据库 | 无法使用 MySQL/PostgreSQL/MongoDB | 使用 JSON 文件作为数据存储 |
| ✅ 静态文件 | HTML/CSS/JS 可直接访问 | 完全支持 |
| ✅ 客户端计算 | 浏览器中执行 JavaScript | 适合数据量小的实时计算 |

### 静态化设计原则

1. **构建时计算** (Build-time Computation)
   - 所有复杂分析在 CI/CD 构建阶段完成
   - 生成静态 JSON 索引文件
   - 前端只做简单的查表操作

2. **分层索引策略**
   ```
   元数据索引 (manifest.json)
   ├── 作者索引 (author_index.json) - 按作者分类
   ├── 朝代索引 (dynasty_index.json) - 按朝代分类
   ├── 搜索索引 (search_index.json) - 倒排索引
   └── 相似度索引 (similarity_index.json) - 预计算相似度
   ```

3. **按需加载**
   - 首屏只加载必要数据
   - 使用分片加载策略
   - 大索引文件使用 Web Worker 处理

---

## 智能体团队

| 角色 | 职责 | 专长 |
|------|------|------|
| **Static Index Architect** | 静态索引设计 | 索引结构设计、JSON 优化、压缩策略 |
| **Build-time Engineer** | 构建时计算 | 预计算逻辑、CI/CD 集成、数据管道 |
| **NLP Engineer** | 文本分析 | 分词、相似度计算、词性标注 |
| **Frontend Developer** | 前端开发 | 纯前端搜索、虚拟滚动、Web Worker |
| **Performance Engineer** | 性能优化 | 索引压缩、懒加载、缓存策略 |
| **Visualization Engineer** | 可视化 | D3.js、静态图表、交互式网络图 |
| **QA Engineer** | 测试 | 端到端测试、性能测试、兼容性测试 |
| **Documentation Writer** | 文档 | 架构文档、API 文档、用户指南 |

---

## 任务清单 (Phase 2 - 静态部署优化版)

### Task 11: 搜索索引生成器
**负责人**: Static Index Architect  
**优先级**: P0 (阻塞其他搜索功能)  
**预估时间**: 3小时

**任务描述**:
- 构建倒排索引 (Inverted Index)
  - 词 -> 诗词ID列表映射
  - 支持中文分词 (jieba)
- 构建作者索引
  - 作者 -> 诗词ID列表
- 构建朝代索引
  - 朝代 -> 诗词ID列表
- 生成压缩后的 JSON 索引文件
- 创建 `scripts/index/build_search_index.py`

**验收标准**:
- [ ] 输出 `data/output/web/index/search_index.json`
- [ ] 输出 `data/output/web/index/author_index.json`
- [ ] 输出 `data/output/web/index/dynasty_index.json`
- [ ] 索引文件总大小 < 原始数据的 30%
- [ ] 支持前缀匹配和精确匹配

**依赖**: Task 3 (Silver层)

**静态化说明**:
```json
// search_index.json 示例
{
  "version": "1.0.0",
  "total_terms": 15000,
  "terms": {
    "明月": [1, 5, 23, 45, ...],
    "故乡": [2, 8, 34, ...],
    "李白": [100, 101, 102, ...]
  },
  "metadata": {
    "compression": "gzip",
    "avg_list_length": 15.5
  }
}
```

---

### Task 12: 词汇相似度索引生成器
**负责人**: NLP Engineer  
**优先级**: P0  
**预估时间**: 4小时

**任务描述**:
- 预计算所有词汇对的相似度
- 使用 TF-IDF + Cosine Similarity
- 只保留相似度 > 0.3 的结果
- 生成词汇相似度索引
- 创建 `scripts/index/build_word_similarity_index.py`

**验收标准**:
- [ ] 输出 `data/output/web/index/word_similarity_index.json`
- [ ] 包含词汇 -> Top 20 相似词汇映射
- [ ] 文件大小 < 10MB (通过阈值过滤)
- [ ] 解决当前相似度为0的问题

**依赖**: Task 3 (Silver层)

**静态化说明**:
```json
// word_similarity_index.json 示例
{
  "version": "1.0.0",
  "total_words": 5000,
  "similarities": {
    "月": [
      {"word": "明", "score": 0.85},
      {"word": "光", "score": 0.72},
      {"word": "影", "score": 0.68}
    ],
    "山": [
      {"word": "水", "score": 0.91},
      {"word": "峰", "score": 0.83}
    ]
  }
}
```

---

### Task 13: 作者相似度索引生成器
**负责人**: NLP Engineer  
**优先级**: P0  
**预估时间**: 3小时

**任务描述**:
- 预计算所有作者间的相似度
- 基于用词习惯 (TF-IDF 向量)
- 为每位作者找出 Top 20 相似作者
- 生成作者相似度网络数据
- 创建 `scripts/index/build_author_similarity_index.py`

**验收标准**:
- [ ] 输出 `data/output/web/index/author_similarity_index.json`
- [ ] 输出网络图数据 `author_network.json`
- [ ] 包含作者 -> Top 20 相似作者
- [ ] 网络图数据兼容 D3.js

**依赖**: Task 3 (Silver层)

**静态化说明**:
```json
// author_similarity_index.json 示例
{
  "version": "1.0.0",
  "total_authors": 623,
  "similarities": {
    "李白": [
      {"author": "杜甫", "score": 0.88, "common_words": ["月", "山", "酒"]},
      {"author": "王维", "score": 0.75, "common_words": ["山", "水", "云"]}
    ]
  },
  "network": {
    "nodes": [{"id": "李白", "group": 1, "poem_count": 50}, ...],
    "links": [{"source": "李白", "target": "杜甫", "value": 0.88}, ...]
  }
}
```

---

### Task 14: 纯前端搜索组件
**负责人**: Frontend Developer  
**优先级**: P1  
**预估时间**: 4小时

**任务描述**:
- 实现基于索引的纯前端搜索
- 支持多关键词组合查询 (AND/OR)
- 支持按作者/朝代筛选
- 使用 Web Worker 处理大索引
- 创建 `data/output/web/js/search_engine.js`

**验收标准**:
- [ ] 首屏加载 < 2秒
- [ ] 搜索结果返回 < 100ms
- [ ] 支持 30万首诗词的搜索
- [ ] 内存占用 < 100MB

**依赖**: Task 11 (搜索索引)

**技术方案**:
```javascript
// search_engine.js 核心逻辑
class StaticSearchEngine {
  async init() {
    // 加载索引
    this.index = await this.loadIndex('index/search_index.json');
    this.authorIndex = await this.loadIndex('index/author_index.json');
  }
  
  search(query, filters = {}) {
    // 使用倒排索引快速查找
    const termIds = this.index.terms[query] || [];
    // 交集/并集运算
    return this.intersect(termIds, filters);
  }
}
```

---

### Task 15: 作者相似度搜索页面
**负责人**: Frontend Developer  
**优先级**: P1  
**预估时间**: 3小时

**任务描述**:
- 实现作者相似度查询页面
- 输入作者名，显示相似作者列表
- 展示共同词汇标签
- 纯前端实现，无需后端API
- 创建 `data/output/web/author-similarity.html`

**验收标准**:
- [ ] 页面可独立访问
- [ ] 支持作者名自动补全
- [ ] 显示相似度分数和共同词汇
- [ ] 响应式设计

**依赖**: Task 13 (作者相似度索引)

**静态化说明**:
- 所有数据来自 `author_similarity_index.json`
- 前端只做数据展示，无实时计算

---

### Task 16: 交互式相似度网络图
**负责人**: Visualization Engineer  
**优先级**: P1  
**预估时间**: 4小时

**任务描述**:
- 使用 D3.js 实现力导向图
- 节点：作者，大小基于诗词数量
- 边：相似度 > 0.5 的连接
- 支持点击节点查看详情
- 支持缩放和拖拽
- 创建 `data/output/web/similarity-network.html`

**验收标准**:
- [ ] 支持 500+ 节点流畅渲染
- [ ] 交互响应 < 16ms (60fps)
- [ ] 支持节点筛选 (按朝代/诗词数量)
- [ ] 移动端手势支持

**依赖**: Task 13 (作者相似度网络数据)

**性能优化**:
```javascript
// 使用 Canvas 渲染大量节点
const canvas = d3.select("#graph")
  .append("canvas")
  .attr("width", width)
  .attr("height", height);

// 力导向模拟
const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id))
  .force("charge", d3.forceManyBody().strength(-100))
  .force("center", d3.forceCenter(width / 2, height / 2));
```

---

### Task 17: 词性标注分析器 (静态化)
**负责人**: NLP Engineer  
**优先级**: P2  
**预估时间**: 4小时

**任务描述**:
- 使用 jieba.posseg 进行词性标注
- 统计每位作者的词性使用偏好
- 预计算词性分布数据
- 生成词性统计索引
- 创建 `scripts/index/build_pos_index.py`

**验收标准**:
- [ ] 输出 `data/output/web/index/pos_index.json`
- [ ] 包含每位作者的词性分布
- [ ] 支持按词性筛选诗词
- [ ] 文件大小 < 5MB

**依赖**: Task 3 (Silver层)

**静态化说明**:
```json
// pos_index.json 示例
{
  "version": "1.0.0",
  "pos_tags": {
    "n": "名词",
    "v": "动词",
    "a": "形容词"
  },
  "authors": {
    "李白": {
      "total_words": 5000,
      "distribution": {
        "n": 0.35,
        "v": 0.28,
        "a": 0.15
      },
      "top_words": {
        "n": ["月", "山", "酒"],
        "v": ["看", "思", "归"]
      }
    }
  }
}
```

---

### Task 18: 诗词推荐系统 (静态化)
**负责人**: NLP Engineer + Frontend Developer  
**优先级**: P2  
**预估时间**: 4小时

**任务描述**:
- 预计算每首诗的相似诗词 (Top 10)
- 基于词汇重叠和风格相似度
- 生成推荐索引
- 前端实现"喜欢这首诗的人也喜欢"功能
- 创建 `scripts/index/build_recommendation_index.py`

**验收标准**:
- [ ] 输出 `data/output/web/index/recommendation_index.json`
- [ ] 每首诗有 10 个推荐
- [ ] 推荐质量通过人工抽样验证
- [ ] 文件大小 < 20MB

**依赖**: Task 3 (Silver层), Task 12 (词汇相似度)

**静态化说明**:
```json
// recommendation_index.json 示例
{
  "version": "1.0.0",
  "recommendations": {
    "poem_123": [
      {"id": "poem_456", "score": 0.85, "reason": "共同词汇: 月, 故乡"},
      {"id": "poem_789", "score": 0.72, "reason": "风格相似"}
    ]
  }
}
```

---

### Task 19: 格律大全页面
**负责人**: Frontend Developer  
**优先级**: P2  
**预估时间**: 3小时

**任务描述**:
- 展示诗词格律统计
- 按格律类型分类浏览
- 支持格律模式搜索 (如 7,7,7,7)
- 纯前端实现
- 创建 `data/output/web/meter-gallery.html`

**验收标准**:
- [ ] 展示所有格律类型统计
- [ ] 支持按格律筛选诗词
- [ ] 显示格律模式可视化
- [ ] 响应式设计

**依赖**: Task 3 (Silver层结构化数据)

**数据说明**:
- 使用 `v2_poems_structured.csv` 中的 `meter_pattern` 字段
- 预计算格律统计信息

---

### Task 20: 完整数据索引构建与测试
**负责人**: Build-time Engineer + QA Engineer  
**优先级**: P2  
**预估时间**: 5小时

**任务描述**:
- 使用完整数据集 (30万+诗词) 构建所有索引
- 优化索引压缩算法
- 测试索引加载性能
- 验证所有前端功能在完整数据下的表现
- 创建 `scripts/index/build_all_indexes.py`

**验收标准**:
- [ ] 所有索引文件总大小 < 100MB
- [ ] 首屏加载时间 < 3秒
- [ ] 搜索响应时间 < 200ms
- [ ] 内存占用 < 200MB
- [ ] 生成性能测试报告

**依赖**: Task 11, 12, 13, 17, 18

**性能目标**:
| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 首屏加载 | < 3s | Lighthouse |
| 搜索响应 | < 200ms | Chrome DevTools |
| 内存占用 | < 200MB | Performance Monitor |
| 索引文件总大小 | < 100MB | 文件系统统计 |

---

## 任务依赖图 (静态部署版)

```
Task 3 (Silver层结构化数据)
    │
    ├─────────────┬─────────────┬─────────────┬─────────────┐
    ▼             ▼             ▼             ▼             ▼
Task 11       Task 12       Task 13       Task 17       Task 18
(搜索索引)    (词汇相似度)   (作者相似度)   (词性标注)     (推荐系统)
    │             │             │             │             │
    ▼             │             ▼             │             │
Task 14 ◄─────────┘             ▼             │             │
(前端搜索)                    Task 15         │             │
                                  (作者相似度页面)            │
                                  │                         │
                                  ▼                         │
                              Task 16                       │
                              (相似度网络图)                 │
                                                            │
Task 19 (格律大全) ◄────────────────────────────────────────┘
    │
    └─────────────┬─────────────────────────────────────────┐
                  ▼                                         ▼
            Task 20 (完整数据索引构建与测试)
```

---

## 执行顺序

| 阶段 | 任务 | 说明 |
|------|------|------|
| **第1波** | Task 11, 12, 13 | 构建核心索引 (搜索、词汇相似度、作者相似度) |
| **第2波** | Task 14, 15, 16 | 前端搜索功能和可视化 |
| **第3波** | Task 17, 18, 19 | 高级功能 (词性、推荐、格律) |
| **第4波** | Task 20 | 完整数据测试和性能优化 |

---

## 索引文件总览

| 索引文件 | 生成任务 | 大小预估 | 用途 |
|----------|----------|----------|------|
| `search_index.json` | Task 11 | ~15MB | 全文搜索 |
| `author_index.json` | Task 11 | ~2MB | 作者筛选 |
| `dynasty_index.json` | Task 11 | ~1MB | 朝代筛选 |
| `word_similarity_index.json` | Task 12 | ~8MB | 词汇相似度查询 |
| `author_similarity_index.json` | Task 13 | ~5MB | 作者相似度查询 |
| `author_network.json` | Task 13 | ~3MB | 网络图可视化 |
| `pos_index.json` | Task 17 | ~4MB | 词性统计 |
| `recommendation_index.json` | Task 18 | ~20MB | 诗词推荐 |
| **总计** | - | **~58MB** | - |

---

## 技术栈

### 构建时 (Build-time)
- Python 3.13+
- jieba (中文分词)
- scikit-learn (TF-IDF, 相似度计算)
- pandas (数据处理)

### 运行时 (Runtime - 纯前端)
- Vanilla JavaScript (ES6+)
- D3.js (可视化)
- Web Worker (后台处理)
- Service Worker (缓存)

---

## 分支策略

```bash
# 创建 Phase 2 分支
git checkout -b refactor/static-deployment-v2

# 每个任务完成后提交
git add .
git commit -m "feat(Task 11): implement search index builder"

# 推送到远程
git push origin refactor/static-deployment-v2

# 完成后创建 PR
gh pr create --title "feat: static deployment optimization" \
  --body "Phase 2: 纯静态部署优化，包含搜索索引、相似度查询、推荐系统"
```

---

## 验收流程

1. **索引构建测试**: 验证所有索引文件正确生成
2. **前端功能测试**: 手动验证搜索、相似度查询、推荐功能
3. **性能测试**: 使用 Lighthouse 和 Chrome DevTools
4. **完整数据测试**: 使用 30万首诗词数据集
5. **GitHub Pages 部署测试**: 验证线上环境表现

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 索引文件过大 | 使用压缩、阈值过滤、分层加载 |
| 首屏加载慢 | 代码分割、懒加载、Service Worker 缓存 |
| 搜索性能差 | Web Worker、索引分片、增量加载 |
| 内存溢出 | 虚拟滚动、大数据集分页、及时释放 |

---

## 与 Phase 1 的差异

| 方面 | Phase 1 | Phase 2 (静态部署版) |
|------|---------|---------------------|
| 部署方式 | 混合 (静态+API) | 纯静态 |
| 相似度计算 | 实时 API 计算 | 预计算索引 |
| 搜索 | 后端搜索 | 纯前端搜索 |
| 推荐 | 实时推荐 | 预计算推荐 |
| 复杂度 | 需要维护后端 | 仅需构建时计算 |
| 成本 | 需要服务器 | 免费 (GitHub Pages) |
| 扩展性 | 受限于服务器性能 | 受限于构建时间 |
