# AI 开发接班人指南

> 本项目的中国古诗词数据挖掘工具，由人类开发者与 AI 助手共同维护。
> 本指南记录开发规范、重构策略和协作风格，帮助未来的 AI 助手快速上手。
> **最后更新**: 2026-03-15

---

## 📋 项目概览

| 项目 | 内容 |
|------|------|
| **名称** | 中国古代文学时空图谱 - 中国古诗词数据挖掘 |
| **核心功能** | 基于 33 万首古诗词的数据挖掘与可视化分析 |
| **技术栈** | Python + Pandas + Plotly + PyTorch/Transformers + NetworkX |
| **数据规模** | 33 万+ 首诗，覆盖唐、宋、元、明、清等朝代 |

### 项目结构
```
chinese-poetry-data-mining/
├── data/                      # 数据目录
│   ├── sample_data/          # 采样数据 (~300首，用于快速测试)
│   └── processed_data/       # 完整数据 (~33万首)
├── src/                       # 源代码
│   ├── core/                 # 核心工具（文本处理、拼音）
│   ├── features/             # 特征提取（韵律、情感）
│   ├── models/               # 分析模型（分类器、社交网络）
│   └── visualization/        # 可视化工具
├── scripts/                   # 执行脚本（按序号组织）
│   ├── 01_data_process.py    # 数据处理
│   ├── 02_analysis_*.py      # 分析脚本（情感、网络、格律）
│   ├── 03_vis_*.py           # 可视化脚本
│   ├── 03_generate_all.py    # 一键运行所有脚本
│   ├── 04_build_index.py     # 构建索引页面
│   └── 04_serve.py           # 本地服务器
├── reports/                   # 分析报告
│   ├── sample/               # sample 数据的结果
│   └── full/                 # full 数据的结果
├── web/                       # Web 前端 (Vue 3 + Vite)
└── docs/                      # 项目文档
```

---

## 🎯 开发原则

### 核心原则

1. **简洁优于复杂**
   - 不要过度工程化
   - 能用简单方法解决的，不要用复杂框架
   - 代码要易读易维护

2. **渐进式改进**
   - 先让代码跑起来，再优化
   - 小步快跑，频繁验证
   - 不要一次性改动太多文件

3. **实用主义**
   - 优先解决实际问题
   - 不要为了追求新技术而使用新技术
   - 文档和代码要对齐

### 代码风格

- **命名**: 清晰、有意义，使用下划线命名法（snake_case）
- **注释**: 中文注释，解释"为什么"而不是"做什么"
- **函数**: 单一职责，参数明确，有返回值说明
- **错误处理**: 优雅降级，给出清晰的错误信息

### 沟通风格

- 主要使用**中文**
- 喜欢**直接、简洁**的沟通
- 重视**实际结果**，不喜欢过度理论化
- 会给出明确的方向，但允许 AI 自主决策实现细节

---

## 🛠️ 开发规范

### 1. 环境管理

**使用 Conda（推荐）**
```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate poetry-mining

# 验证安装
python -c "import torch; print(torch.__version__)"
```

**关键依赖版本约束**
- `numpy=1.24` - 兼容性考虑
- `setuptools=69.5.1` - node2vec 需要旧版 pkg_resources
- `pandas=2.0` - 稳定版本

### 2. 脚本开发规范

#### 参数设计
所有脚本必须支持以下参数：
```python
parser.add_argument('--data', choices=['sample', 'full'], default='sample',
                   help='使用 sample 或 full 数据')
parser.add_argument('--override', action='store_true',
                   help='覆盖已有结果（用于缓存刷新）')
```

#### 输出路径规范
```python
# 根据数据类型保存到不同子目录
output_dir = project_root / "reports" / args.data / "analysis_name"
output_dir.mkdir(parents=True, exist_ok=True)
```

#### 缓存策略
- 使用 MD5 哈希生成缓存键
- 缓存位置: `data/cache/`
- 默认跳过已存在的结果，除非使用 `--override`

### 3. 数据流设计

```
原始数据 (chinese-poetry JSON)
    ↓
01_data_process.py → sample_data/ & processed_data/
    ↓
02_analysis_*.py → reports/{sample,full}/analysis/
    ↓
03_vis_*.py → reports/{sample,full}/visualizations/
    ↓
04_build_index.py → reports/{sample,full}/visualizations/index.html
```

---

## 🔄 重构策略

### 何时重构

1. **功能重复** - 多个脚本有相似代码
2. **路径混乱** - 输入输出路径不一致
3. **参数缺失** - 不支持 sample/full 切换
4. **命名不清** - 脚本名不能反映功能

### 重构步骤

1. **分析现状**
   - 列出所有相关文件
   - 识别重复代码
   - 确定改进目标

2. **制定方案**
   - 与现有方案对比（如方案 A vs 方案 B）
   - 考虑向后兼容性
   - 预估改动范围

3. **执行重构**
   - 一次只改一个脚本
   - 改完后立即测试
   - 更新相关引用（README、workflow 等）

4. **验证结果**
   - 运行完整流程
   - 检查输出路径
   - 确认 GitHub Actions 能正常工作

---

## 📝 Commit 规范

### 分批 Commit 策略

不要一次性提交所有改动，按逻辑分批：

1. **环境配置** - `environment.yml`, `.gitignore`
2. **核心功能** - 02 系列分析脚本
3. **可视化** - 03 系列可视化脚本
4. **工具脚本** - 重命名、重构
5. **CI/CD** - GitHub Actions workflow
6. **文档** - README, docs/
7. **生成文件** - reports/, data/

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [01-web-design.md](./01-web-design.md) | Web 前端创意设计方案 |
| [02-data-pipeline.md](./02-data-pipeline.md) | 数据处理管线说明 |
| [03-deployment.md](./03-deployment.md) | GitHub Actions 部署方案 |
| [04-research-author-similarity.md](./04-research-author-similarity.md) | 诗人相似度研究验证 |
