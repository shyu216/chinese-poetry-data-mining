# 2026-03-13 Phase 1 任务规划

## 智能体团队设计

| 角色 | 职责 |
|------|------|
| Data Architect | Schema设计、数据建模 |
| Pipeline Engineer | ETL流程、数据处理 |
| NLP Engineer | 分词、相似度计算 |
| Frontend Developer | HTML/CSS/JS、D3.js |
| Backend Developer | Flask API、数据库 |
| DevOps Engineer | CI/CD、自动化部署 |
| QA Engineer | 单元测试、集成测试 |
| Performance Engineer | 分片加载、虚拟滚动 |

## 核心任务

### Task 1: 数据Schema定义 (P0)
- Pydantic数据模型
- PoemBase, PoemRaw, PoemProcessed, PoemWithAnalysis
- Genre, PoemType枚举

### Task 2: Bronze层清洗脚本 (P0)
- 加载chinese-poetry数据
- 统一字段名、繁简转换
- 去重、生成采样数据

### Task 3: Silver层结构化 (P0)
- 解析诗句结构
- 提取格律模式
- 判断诗体类型

### Task 4: 文本相似度分析器 (P1)
- TF-IDF向量化
- Cosine Similarity计算
- Top 10相似作者

## 关键约束

- 支持--data sample|full参数
- 支持--force参数强制重跑
- 所有模型通过mypy类型检查
