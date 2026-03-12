# 中国古典诗词数据库 - 项目进度报告

**日期**: 2026-03-12  
**项目**: chinese-poetry-data-mining  
**状态**: 活跃开发中

---

## 📊 项目概览

基于 chinese-poetry 开源数据集，构建33万首古典诗词的数据挖掘与可视化平台。

### 核心数据
| 指标 | 数值 |
|------|------|
| 诗词总数 | 332,602 首 |
| 格律模式 | 16,471 种 |
| 朝代覆盖 | 唐、宋、元、明、清等 |
| 体裁分布 | 诗、词、曲 |

---

## ✅ 已完成任务

### 1. 数据处理 (100%)
- [x] 繁简转换 (使用 OpenCC)
- [x] 句式分析 (paragraphs → lines)
- [x] 格律提取 (meter_pattern: 7,7,7,7)
- [x] 数据清洗 (去除标点，保留中文字符)

**产出文件**:
- `data/structure_analysis/poetry_structure_full.csv` (33万首)
- `data/structure_analysis/poetry_structure_sample.csv` (331首)

### 2. 格律分析 (100%)
- [x] 统计16,471种格律模式
- [x] 位置词性分析 (高频字、词性分布)
- [x] 筛选高频格律 (count ≥ 100，共113种)

**产出文件**:
- `data/meter_position_stats.json`

### 3. 情感分析 (100%)
- [x] 基于BERT的情感分析
- [x] 朝代情感分布
- [x] 作者情感分布

**产出文件**:
- `data/cache/sentiment_*.json`
- `reports/sample/sentiment_analysis/author_sentiment.json`

### 4. 社交网络分析 (100%)
- [x] 诗人关系网络构建
- [x] 中心性分析 (度、介数、PageRank)
- [x] 聚类分析

**产出文件**:
- `data/cache/network_*.json`
- `reports/sample/social_network/network_analysis.json`

### 5. 可视化 (100%)
- [x] Plotly 交互式图表
- [x] 作者、朝代、格律、情感、网络可视化
- [x] 网络图、热力图、散点图

**产出文件**:
- `reports/sample/visualizations/*.html`

### 6. GitHub Pages 静态站点 (90%)
- [x] 数据导出 (JSON格式)
- [x] 格律大全页面 (搜索、分页、位置分析)
- [x] 竖排诗词展示 (传统排版)
- [x] 总入口页面
- [ ] 完整33万诗词加载 (需优化性能)

**产出文件**:
- `data/github_pages/index.html` (总入口)
- `data/github_pages/meter/index.html` (格律大全)
- `data/github_pages/data/*.json` (数据文件)

### 7. API 服务 (80%)
- [x] Flask REST API
- [x] 诗词查询接口
- [x] 格律统计接口
- [x] 位置分析接口
- [ ] 全文搜索 (待实现)

### 8. 综合测试 (100%) - 2026-03-12
- [x] Pandas/NumPy 数据处理测试
- [x] OpenCC/pypinyin 文本处理测试
- [x] Plotly 可视化测试
- [x] scikit-learn TF-IDF 和聚类测试
- [x] NetworkX 社交网络分析测试
- [x] gensim Word2Vec 测试
- [x] 测试脚本开发

**产出文件**:
- `scripts/test/test_all_libraries.py`
- `scripts/test/test_poem_visualization.html`
- `scripts/test/test_network.png`

---

## 🚧 进行中任务

### 高优先级
1. **诗词竖排排版优化**
   - 长诗换行显示 (flex-wrap)
   - 标题、标签、作者全部竖排
   - 响应式布局

2. **性能优化**
   - 33万诗词分块加载
   - 虚拟滚动
   - 数据压缩 (gzip)

### 中优先级
3. **诗词检索功能**
   - 全文搜索
   - 按作者、朝代筛选
   - 模糊匹配

4. **数据可视化**
   - 诗人关系网络
   - 朝代诗词分布
   - 格律演变趋势

---

## 📁 项目结构

```
chinese-poetry-data-mining/
├── data/
│   ├── chinese-poetry/          # 原始数据 (git submodule)
│   ├── chinese-gushiwen/        # 古诗文网数据
│   ├── sample_data/             # 采样数据 (331首)
│   ├── cache/                   # 缓存数据
│   └── gh-pages/                # GitHub Pages 部署文件
│       ├── index.html           # 主入口
│       ├── sample/              # Sample 数据版本
│       └── full/                # Full 数据版本
│
├── src/
│   ├── core/                    # 核心工具
│   │   ├── text_utils.py        # 文本处理 (OpenCC)
│   │   └── pinyin_utils.py      # 拼音工具 (pypinyin)
│   ├── features/                # 特征提取
│   │   └── rhyme_features.py    # 韵律特征
│   ├── models/                  # 分析模型
│   │   ├── poetry_classifier.py # 诗词分类器
│   │   └── social_network_model.py # 社交网络模型
│   └── visualization/           # 可视化工具
│       └── poetry_visualizer.py # 诗词可视化
│
├── scripts/
│   ├── 01_data_process.py       # 数据处理
│   ├── 02_analysis_meter.py     # 格律分析
│   ├── 02_analysis_network.py   # 社交网络分析
│   ├── 02_analysis_sentiment.py # 情感分析
│   ├── 03_vis_author.py         # 作者可视化
│   ├── 03_vis_dynasty.py        # 朝代可视化
│   ├── 03_vis_meter.py          # 格律可视化
│   ├── 03_vis_network.py        # 网络可视化
│   ├── 03_vis_sentiment.py      # 情感可视化
│   ├── 03_generate_all.py       # 运行所有脚本
│   ├── 04_build_index.py        # 构建索引
│   ├── 04_serve.py              # 本地服务器
│   └── test/                    # 测试脚本
│       └── test_all_libraries.py # 综合测试
│
├── reports/
│   ├── sample/                  # 采样数据报告
│   │   ├── meter_analysis/      # 格律分析
│   │   ├── sentiment_analysis/ # 情感分析
│   │   ├── social_network/      # 社交网络
│   │   └── visualizations/      # 可视化图表
│   └── full/                    # 完整数据报告
│
├── docs/                        # 文档
│   ├── PROJECT_STATUS.md        # 项目状态
│   ├── 2026-03-11-*.md          # 历史文档
│   └── 2026-03-12-*.md          # 今日文档
│
├── .github/workflows/           # CI/CD
│   └── deploy-pages.yml         # GitHub Pages 部署
│
├── environment.yml              # Conda 环境配置
├── requirements.txt             # pip 依赖
└── README.md                    # 项目说明
```

---

## 🚀 快速开始

### 本地开发
```bash
# 1. 启动 API 服务
python scripts/05_api_server.py

# 2. 启动静态文件服务器
cd data/github_pages
python -m http.server 8080

# 3. 访问
# http://localhost:8080/index.html
```

### 部署到 GitHub Pages
```bash
# 1. 导出数据
python scripts/08_export_github_pages.py

# 2. 推送到 GitHub
# Settings → Pages → 选择 main 分支
```

---

## 📈 关键成果

### 格律统计发现
| 格律模式 | 数量 | 类型 |
|---------|------|-----|
| 7,7,7,7 | 81,806 | 七言绝句 |
| 7,7,7,7,7,7,7,7 | 65,896 | 七言律诗 |
| 5,5,5,5,5,5,5,5 | 58,865 | 五言律诗 |
| 5,5,5,5 | 16,932 | 五言绝句 |

### 位置分析示例 (七言绝句)
| 位置 | 高频字 | 词性 |
|-----|--------|-----|
| 第1字 | 不、一、只 | 动/副 |
| 第2字 | 人、来、是 | 名/动 |
| 第3字 | 不、无、风 | 动/名 |
| 第4字 | 人、来、风 | 名/动 |

---

## 🎯 下一步计划

### 本周 (3月12日-3月19日)
1. [ ] 优化诗词竖排排版 (长诗换行)
2. [ ] 实现诗词全文搜索
3. [ ] 添加诗人关系网络图
4. [ ] 完善 GitHub Pages 部署文档

### 本月
1. [ ] 33万诗词完整加载方案
2. [ ] 数据可视化仪表盘
3. [ ] 用户反馈收集
4. [ ] 性能优化 (加载速度 < 3s)

---

## 🛠️ 技术栈

| 类别 | 技术 | 状态 |
|-----|------|------|
| 数据处理 | Python 3.11, Pandas, NumPy | ✅ 充分使用 |
| 文本处理 | OpenCC, pypinyin, jieba | ✅ 充分使用 |
| 可视化 | Plotly, Pyecharts, Dash | ✅ 充分使用 |
| 机器学习 | scikit-learn (TF-IDF, 聚类) | ✅ 充分使用 |
| 深度学习 | PyTorch, Transformers (BERT) | ✅ 充分使用 |
| 网络分析 | NetworkX, Node2Vec | ✅ 充分使用 |
| 词向量 | gensim (Word2Vec) | ✅ 已测试 |
| 后端 API | Flask, Flask-CORS | ✅ 已实现 |
| 前端 | HTML5, CSS3, JavaScript | ✅ 已实现 |
| 部署 | GitHub Pages, GitHub Actions | ✅ 已配置 |
| NER | HanLP | ❌ 计划添加 |
| 时间解析 | JioNLP | ❌ 计划添加 |

---

## 📝 备注

- 数据基于 chinese-poetry 开源项目
- 所有数据处理已完成繁简转换
- 格律分析覆盖 88.8% 的诗词 (count ≥ 100)
- 静态站点适合部署到任何 CDN

---

**最后更新**: 2026-03-12  
**维护者**: LMAPA
