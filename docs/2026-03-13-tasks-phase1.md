# 任务分配 - 2026-03-13

**项目**: chinese-poetry-data-mining  
**分支**: refactor/pipeline-v2  
**状态**: 待分配

---

## 智能体团队

| 角色 | 职责 | 专长 |
|------|------|------|
| **Data Architect** | 数据架构设计 | Schema设计、数据建模、Pydantic |
| **Pipeline Engineer** | 管线开发 | ETL流程、数据处理、增量更新 |
| **NLP Engineer** | 文本分析 | 分词、相似度计算、词性标注 |
| **Frontend Developer** | 前端开发 | HTML/CSS/JS、D3.js、Plotly |
| **Backend Developer** | 后端开发 | Flask API、数据库、缓存 |
| **DevOps Engineer** | CI/CD | GitHub Actions、自动化部署 |
| **QA Engineer** | 测试 | 单元测试、集成测试、性能测试 |
| **Documentation Writer** | 文档 | README、API文档、用户指南 |
| **Performance Engineer** | 性能优化 | 分片加载、虚拟滚动、采样 |
| **Security Engineer** | 安全 | 数据验证、敏感信息、权限控制 |

---

## 任务清单

### Task 1: 数据Schema定义
**负责人**: Data Architect  
**优先级**: P0 (阻塞其他任务)  
**预估时间**: 2小时

**任务描述**:
- 定义 Pydantic 数据模型
- 包含: PoemBase, PoemRaw, PoemProcessed, PoemWithAnalysis
- 定义 Genre, PoemType 枚举
- 创建 `src/schema/poetry.py`

**验收标准**:
- [ ] 所有模型通过 mypy 类型检查
- [ ] 包含字段验证逻辑
- [ ] 支持 JSON 序列化/反序列化

**依赖**: 无

---

### Task 2: Bronze层清洗脚本
**负责人**: Pipeline Engineer  
**优先级**: P0  
**预估时间**: 4小时

**任务描述**:
- 加载 chinese-poetry submodule 数据
- 统一诗/词/曲字段名
- 繁简转换 (OpenCC)
- 去重 (基于 hash)
- 生成采样数据 (1/1000)
- 创建 `scripts/steps/01_clean.py`

**验收标准**:
- [ ] 输出 `data/bronze/v1_poems_merged.csv`
- [ ] 输出 `data/bronze/v1_metadata.json`
- [ ] 支持 --data sample|full 参数
- [ ] 支持 --force 参数强制重跑

**依赖**: Task 1

---

### Task 3: Silver层结构化脚本
**负责人**: Pipeline Engineer  
**优先级**: P0  
**预估时间**: 3小时

**任务描述**:
- 解析诗句结构
- 提取格律模式 (如 7,7,7,7)
- 判断是否格律诗
- 分类诗体 (七言绝句/五言律诗等)
- 创建 `scripts/steps/02_structure.py`

**验收标准**:
- [ ] 输出 `data/silver/v2_poems_structured.csv`
- [ ] 包含 lines, meter_pattern, is_regular, poem_type 字段
- [ ] 统计信息输出到 v2_stats.json

**依赖**: Task 2

---

### Task 4: 文本相似度分析器
**负责人**: NLP Engineer  
**优先级**: P1  
**预估时间**: 4小时

**任务描述**:
- 使用 TF-IDF 向量化作者文档
- 计算 Cosine Similarity
- 为每位作者找出 Top 10 相似作者
- 创建 `src/analyzers/text_similarity.py`

**验收标准**:
- [ ] 输出相似度矩阵
- [ ] 输出 similar_authors.json
- [ ] 支持 sample/full 数据切换

**依赖**: Task 3

---

### Task 5: 词汇频率分析器
**负责人**: NLP Engineer  
**优先级**: P1  
**预估时间**: 3小时

**任务描述**:
- 使用 jieba 分词
- 筛选实词 (名词/动词/形容词)
- 统计每位作者 Top 100 高频词
- 创建 `src/analyzers/word_frequency.py`

**验收标准**:
- [ ] 输出 author_words.json
- [ ] 排除停用词
- [ ] 支持自定义词性筛选

**依赖**: Task 3

---

### Task 6: Pipeline Orchestrator
**负责人**: Pipeline Engineer  
**优先级**: P1  
**预估时间**: 3小时

**任务描述**:
- 统一管线入口 `scripts/pipeline.py`
- 支持步骤选择 (clean/structure/similarity/words)
- 支持 sample/full 数据切换
- 支持 --force 强制重跑
- 生成执行日志

**验收标准**:
- [ ] 单命令运行完整管线
- [ ] 支持增量执行
- [ ] 错误时中断并提示

**依赖**: Task 2, 3, 4, 5

---

### Task 7: 分片导出器
**负责人**: Performance Engineer  
**优先级**: P1  
**预估时间**: 3小时

**任务描述**:
- 实现分片导出逻辑
- 每片 ≤ 10MB
- 生成 manifest.json
- 创建 `scripts/export/web.py`

**验收标准**:
- [ ] 所有分片文件 < 10MB
- [ ] manifest 包含完整索引
- [ ] 支持增量导出

**依赖**: Task 3

---

### Task 8: 前端渐进式加载
**负责人**: Frontend Developer  
**优先级**: P2  
**预估时间**: 4小时

**任务描述**:
- 实现 ProgressiveLoader 类
- 虚拟滚动 (最多100个DOM节点)
- 分片懒加载
- 创建 `data/github_pages/js/progressive_loader.js`

**验收标准**:
- [ ] 首屏加载 < 1秒
- [ ] 滚动流畅 (60fps)
- [ ] 支持搜索功能

**依赖**: Task 7

---

### Task 9: REST API v2
**负责人**: Backend Developer  
**优先级**: P2  
**预估时间**: 4小时

**任务描述**:
- 实现 Flask Blueprint
- 端点: /similarity, /words, /pos
- 版本控制
- 创建 `scripts/serve.py`

**验收标准**:
- [ ] 所有端点返回正确 JSON
- [ ] 支持 CORS
- [ ] 包含错误处理

**依赖**: Task 4, 5

---

### Task 10: CI/CD Pipeline
**负责人**: DevOps Engineer  
**优先级**: P2  
**预估时间**: 3小时

**任务描述**:
- 重写 `.github/workflows/ci-cd.yml`
- 添加 lint, test, pipeline, deploy 四个 Job
- 细化触发条件
- 支持手动触发

**验收标准**:
- [ ] Push 到 main 自动部署
- [ ] PR 自动运行测试
- [ ] 手动触发支持 sample/full 切换

**依赖**: Task 6, 7, 9

---

## 任务依赖图

```
Task 1 (Schema)
    │
    ▼
Task 2 (Bronze) ─────────────────────────────────┐
    │                                             │
    ▼                                             │
Task 3 (Silver) ─────────────────────────────────┤
    │                                             │
    ├─────────────┬─────────────┐                 │
    ▼             ▼             ▼                 │
Task 4       Task 5       Task 7                 │
(Similarity) (Words)      (Export)               │
    │             │             │                 │
    └─────┬───────┘             │                 │
          │                     │                 │
          ▼                     │                 │
      Task 9 (API) ◄────────────┘                 │
          │                                       │
          └───────────────┬───────────────────────┘
                          │
                          ▼
                    Task 10 (CI/CD)
                          
Task 6 (Orchestrator) ←── Task 2, 3, 4, 5
Task 8 (Frontend) ←── Task 7
```

---

## 执行顺序

| 阶段 | 任务 | 并行度 |
|------|------|--------|
| 1 | Task 1 | 1 |
| 2 | Task 2 | 1 |
| 3 | Task 3 | 1 |
| 4 | Task 4, 5, 7 | 3 (并行) |
| 5 | Task 6, 8, 9 | 3 (并行) |
| 6 | Task 10 | 1 |

---

## 分支策略

```bash
# 创建重构分支
git checkout -b refactor/pipeline-v2

# 每个任务完成后提交
git add .
git commit -m "feat: implement Task N - 描述"

# 推送到远程
git push origin refactor/pipeline-v2

# 完成后创建 PR
gh pr create --title "refactor: pipeline v2" --body "重构数据管线和可视化框架"
```

---

## 验收流程

1. **代码审查**: 每个 PR 需要通过 Code Review
2. **自动化测试**: CI 必须通过
3. **功能测试**: 手动验证核心功能
4. **性能测试**: 确保渲染流畅
5. **文档更新**: 更新 README 和 API 文档
