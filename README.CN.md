# 中国古诗词数据挖掘

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-在线-brightgreen)](https://shyu216.github.io/chinese-poetry-data-mining)

> 🏮 **中国古代文学时空图谱**：基于古诗词的静态站点数据挖掘
>
> 用数据科学方法探索中国古典诗词的隐藏规律。**纯静态部署，无需后端服务。**

[中文版本](README.CN.md) | [English Version](README.md)

---

## 🌟 功能特性

- **🔍 全文搜索**：客户端搜索诗词、作者、朝代
- **👥 作者相似度**：发现写作风格相近的诗人（TF-IDF + 余弦相似度）
- **🕸️ 相似度网络**：交互式 D3.js 诗人关系网络可视化
- **📜 格律大全**：按格律类型浏览诗词
- **🏷️ 词性标注**：分析作者写作风格的词性分布
- **💡 诗词推荐**："喜欢这首诗的人也喜欢"推荐功能
- **🚀 GitHub Pages 集成**：纯静态自动部署

## 🏗️ 架构设计

### 数据分层架构 (Bronze/Silver/Gold)

```
RAW (原始) → BRONZE (清洗) → SILVER (结构化) → GOLD (分析) → OUTPUT (输出)
```

| 层级 | 说明 | 格式 |
|------|------|------|
| **Bronze** | 清洗合并后的数据 | CSV + JSON 元数据 |
| **Silver** | 结构化数据，包含格律提取 | CSV |
| **Gold** | 分析结果（相似度、词频） | JSON |
| **Output** | Web 就绪的静态文件 | JSON 分片 + HTML |

### 静态部署

本项目采用**纯静态部署**：

| 特性 | 传统方案 | 本项目 |
|------|----------|--------|
| 后端服务 | Flask/Django 服务器 | ❌ 无 |
| 数据库 | MySQL/PostgreSQL | ❌ 无 |
| 实时计算 | 服务器端 | ❌ 无 |
| 静态文件 | HTML/CSS/JS | ✅ 是 |
| 客户端计算 | 有限 | ✅ 完整 JavaScript |

**工作原理**：
1. **构建时计算**：所有分析在本地运行，生成静态 JSON 索引
2. **静态索引**：预计算的搜索索引、相似度矩阵、推荐结果
3. **客户端搜索**：使用倒排索引的纯 JavaScript 搜索
4. **GitHub Pages**：直接部署静态文件

## 🛠️ 技术栈

| 类别 | 工具 | 状态 |
|------|------|------|
| 数据处理 | Pandas, NumPy | ✅ 使用 |
| 文本处理 | jieba, pypinyin, OpenCC | ✅ 使用 |
| 相似度计算 | scikit-learn (TF-IDF, 余弦相似度) | ✅ 使用 |
| 可视化 | D3.js, Plotly | ✅ 使用 |
| 前端 | 原生 JS, Web Workers | ✅ 使用 |
| **已移除** | | |
| 深度学习 | PyTorch, Transformers | ❌ 移除（不需要） |
| 社交网络分析 | NetworkX, Node2Vec | ❌ 移除（准确率低） |
| 情感分析 | 自定义模型 | ❌ 移除（准确率低） |

## 📁 项目结构

```
chinese-poetry-data-mining/
├── data/
│   ├── bronze/                # 清洗数据 (v1)
│   ├── silver/                # 结构化数据 (v2)
│   ├── gold/                  # 分析结果 (v3)
│   └── output/web/            # Web 输出 (GitHub Pages)
├── src/
│   ├── analyzers/             # 分析模块
│   ├── config/                # 配置
│   └── schema/                # 数据模型
├── scripts/
│   ├── steps/                 # 数据流水线步骤
│   │   ├── 01_clean.py
│   │   ├── 02_structure.py
│   │   ├── 03_analyze_words.py
│   │   └── 04_analyze_similarity.py
│   ├── index/                 # 索引构建器（静态）
│   │   ├── build_search_index.py
│   │   ├── build_author_similarity_index.py
│   │   ├── build_word_similarity_index.py
│   │   ├── build_pos_index.py
│   │   ├── build_recommendation_index.py
│   │   └── build_all_indexes.py
│   └── export/                # 导出脚本
│       └── web.py
├── docs/                      # 文档
├── archive/legacy/            # 旧版代码（已归档）
└── .github/workflows/         # CI/CD（仅静态部署）
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- pip 或 conda

### 安装

```bash
# 克隆仓库
git clone https://github.com/shyu216/chinese-poetry-data-mining.git
cd chinese-poetry-data-mining

# 安装依赖
pip install -r requirements.txt
```

### 构建数据流水线

```bash
# 运行完整数据流水线（一次性设置）
python scripts/steps/01_clean.py
python scripts/steps/02_structure.py
python scripts/steps/03_analyze_words.py
python scripts/steps/04_analyze_similarity.py

# 构建所有静态索引
python scripts/index/build_all_indexes.py

# 导出 Web 文件
python scripts/export/web.py
```

### 本地开发

```bash
# 启动本地服务器测试
python -m http.server 8080 --directory data/output/web

# 或使用 serve 脚本
python scripts/export/web.py --serve
```

### 查看结果

打开 http://localhost:8080 查看本地静态站点。

## 📊 在线演示

访问我们的 **[GitHub Pages](https://shyu216.github.io/chinese-poetry-data-mining)** 查看在线站点！

**可用功能**：
- 🔍 [智能搜索](https://shyu216.github.io/chinese-poetry-data-mining/search.html)
- 👥 [作者相似度](https://shyu216.github.io/chinese-poetry-data-mining/author-similarity.html)
- 🕸️ [相似度网络](https://shyu216.github.io/chinese-poetry-data-mining/similarity-network.html)
- 📜 [格律大全](https://shyu216.github.io/chinese-poetry-data-mining/meter-gallery.html)

## 📚 文档

| 文档 | 说明 |
|------|------|
| [2026-03-13-plan-refactor.md](docs/2026-03-13-plan-refactor.md) | 重构方案和架构决策 |
| [2026-03-13-tasks-phase1.md](docs/2026-03-13-tasks-phase1.md) | 阶段1任务（数据流水线） |
| [2026-03-13-tasks-phase2.md](docs/2026-03-13-tasks-phase2.md) | 阶段2任务（静态部署） |
| [2026-03-13-report-index-build.txt](docs/2026-03-13-report-index-build.txt) | 索引构建性能报告 |

## 🔄 数据流水线

```bash
# 完整流水线（按顺序运行）
python scripts/steps/01_clean.py        # Bronze 层
python scripts/steps/02_structure.py     # Silver 层  
python scripts/steps/03_analyze_words.py # 词频分析
python scripts/steps/04_analyze_similarity.py # 相似度分析

# 构建静态索引
python scripts/index/build_all_indexes.py

# 导出 Web
python scripts/export/web.py
```

## 🏛️ 架构变更

### 新增功能 (v1.0)

- ✅ **纯静态部署** - 无需后端服务器
- ✅ **客户端搜索** - 倒排索引 + Web Workers
- ✅ **预计算索引** - 构建时计算相似度、推荐
- ✅ **Bronze/Silver/Gold 分层** - 清晰的数据血缘
- ✅ **D3.js 可视化** - 交互式网络图

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 🙏 致谢

- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - 全面的中华古诗词数据库
- [ccpoems](https://github.com/shyu216/ccpoems) - React Native 移动应用配套项目

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

<p align="center">
  <i>通过数据科学探索中国诗词之美 🏮</i>
</p>
