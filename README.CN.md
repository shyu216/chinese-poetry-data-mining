# 中国古诗词数据挖掘

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-在线-brightgreen)](https://shyu216.github.io/chinese-poetry-data-mining)

> 🏮 **中国古代文学时空图谱**：基于33万首古诗词的大数据挖掘
>
> 用数据科学方法探索中国古典诗词的隐藏规律

[中文版本](README_CN.md) | [English Version](README.md)

---

## 🌟 功能特性

- **📊 情感分析**：发现不同朝代、诗人的情感模式
- **🕸️ 社交网络分析**：构建诗人之间的文学关系网络
- **🎵 格律分析**：识别诗体、分析平仄韵律
- **📈 交互式可视化**：使用 Plotly 生成精美图表
- **🚀 GitHub Pages 集成**：自动部署可视化到网页

## 🛠️ 技术栈

| 类别 | 工具 |
|------|------|
| 数据处理 | Pandas, NumPy |
| 文本处理 | OpenCC（繁简转换）, pypinyin（拼音）, jieba（分词） |
| 特征提取 | 自定义韵律、情感、语义提取器 |
| 可视化 | Plotly, Pyecharts, Dash |
| 机器学习 | scikit-learn（TF-IDF、相似度、聚类） |
| 深度学习 | PyTorch, Transformers（BERT） |
| 网络分析 | NetworkX, Node2Vec |

## 📁 项目结构

```
chinese-poetry-data-mining/
├── data/
│   ├── sample_data/           # 采样数据集（331首诗）
│   └── processed_data/        # 完整数据集（33万+首诗）
├── src/
│   ├── core/                  # 核心工具（文本、拼音）
│   ├── features/              # 特征提取（韵律、情感）
│   ├── models/                # 分析模型（分类器、网络）
│   └── visualization/         # 可视化工具
├── scripts/
│   ├── 01_data_process.py     # 数据处理
│   ├── 02_analysis_*.py       # 分析脚本
│   ├── 03_vis_*.py            # 可视化脚本
│   ├── 03_generate_all.py     # 运行所有脚本
│   ├── 04_build_index.py      # 构建可视化索引
│   └── 04_serve.py            # 本地服务器
├── reports/
│   └── visualizations/        # 生成的 HTML 可视化
├── docs/                      # 文档
└── .github/workflows/         # GitHub Pages CI/CD
```

## 🚀 快速开始

### 方式1：Conda（推荐）

```bash
# 克隆仓库
git clone https://github.com/shyu216/chinese-poetry-data-mining.git
cd chinese-poetry-data-mining

# 创建 conda 环境
conda env create -f environment.yml

# 激活环境
conda activate poetry-mining

# 验证安装
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import node2vec; print(f'Node2Vec: {node2vec.__version__}')"
```

**注意：** 默认安装 PyTorch CPU 版本。如需 GPU 支持，请修改 `environment.yml` 使用 `pytorch-gpu` 频道。

### 方式2：pip

```bash
# Python 3.11+
git clone https://github.com/shyu216/chinese-poetry-data-mining.git
cd chinese-poetry-data-mining
pip install -r requirements.txt
```

### 生成可视化

```bash
# 确保 conda 环境已激活
conda activate poetry-mining

# 方式1：一键运行所有脚本
python scripts/03_generate_all.py

# 方式2：单独运行分析脚本
python scripts/02_analysis_sentiment.py --data sample
python scripts/02_analysis_network.py --data sample --node2vec
python scripts/02_analysis_meter.py --data sample

# 方式3：单独运行可视化脚本
python scripts/03_vis_sentiment.py
python scripts/03_vis_network.py
python scripts/03_vis_dynasty.py
```

### 查看结果

```bash
# 启动本地服务器
python scripts/04_serve.py

# 或直接打开
open reports/visualizations/index.html
```

## 📊 在线演示

访问 **[GitHub Pages](https://shyu216.github.io/chinese-poetry-data-mining)** 查看交互式可视化！

![情感分析](docs/assets/sentiment-preview.png)
*示例：331首古诗词的情感分布*

## 📚 文档

- [开发进度](docs/2026-03-11-progress.md) - 初始开发日志
- [重构记录](docs/2026-03-11-refactor.md) - 代码重构文档

## 🤝 贡献指南

欢迎提交 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 🙏 致谢

- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - 全面的中国古诗词 JSON 数据库
- [ccpoems](https://github.com/shyu216/ccpoems) - React Native 移动端配套项目

##  开源协议

本项目采用 MIT 协议开源 - 详见 [LICENSE](LICENSE) 文件

---

<p align="center">
  <i>用数据科学探索中国诗词之美 🏮</i>
</p>
