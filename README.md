# Chinese Poetry Data Mining

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://shyu216.github.io/chinese-poetry-data-mining)

> 🏮 **Chinese Ancient Literature Atlas**: Data Mining over 330K Classical Poems
>
> Discover hidden patterns in ancient Chinese literature through data science

[中文版本](README.CN.md) | [English Version](README.md)

---

## 🌟 Features

- **📊 Sentiment Analysis**: Uncover emotional patterns across dynasties and poets
- **🕸️ Social Network Analysis**: Map literary connections between poets
- **🎵 Meter & Rhyme Analysis**: Identify poetic forms and tonal patterns
- **📈 Interactive Visualizations**: Beautiful Plotly charts and dashboards
- **🚀 GitHub Pages Integration**: Auto-deploy visualizations to the web

## 🛠️ Tech Stack

| Category | Tools | Status |
|----------|-------|--------|
| Data Processing | Pandas, NumPy | ✅ Fully Used |
| Text Processing | OpenCC (Traditional/Simplified), pypinyin, jieba | ✅ Fully Used |
| Feature Extraction | Custom rhyme, sentiment, semantic extractors | ✅ Implemented |
| Visualization | Plotly, Pyecharts, Dash | ✅ Fully Used |
| Machine Learning | scikit-learn (TF-IDF, similarity, clustering) | ✅ Fully Used |
| Deep Learning | PyTorch, Transformers (BERT) | ✅ Fully Used |
| Network Analysis | NetworkX, Node2Vec | ✅ Fully Used |
| Word Embeddings | gensim (Word2Vec) | ✅ Tested |
| NER | HanLP | ❌ Planned |
| Time Parsing | JioNLP | ❌ Planned |

## 📁 Project Structure

```
chinese-poetry-data-mining/
├── data/
│   ├── sample_data/           # Sample dataset (331 poems)
│   └── processed_data/        # Full dataset (330K+ poems)
├── src/
│   ├── core/                  # Core utilities (text, pinyin)
│   ├── features/              # Feature extraction (rhyme, sentiment)
│   ├── models/                # Analysis models (classifier, network)
│   └── visualization/         # Visualization tools
├── scripts/
│   ├── 01_data_process.py     # Data processing
│   ├── 02_analysis_*.py       # Analysis scripts
│   ├── 03_vis_*.py            # Visualization scripts
│   ├── 03_generate_all.py     # Run all scripts
│   ├── 04_build_index.py      # Build visualization index
│   ├── 04_serve.py            # Local server
│   └── test/                  # Test scripts
│       └── test_all_libraries.py # Comprehensive library tests
├── reports/
│   └── visualizations/        # Generated HTML visualizations
├── docs/                      # Documentation
│   ├── PROJECT_STATUS.md      # Project status
│   └── 2026-03-12-summary.md  # Daily progress summary
└── .github/workflows/         # CI/CD for GitHub Pages
```

## 🚀 Quick Start

### Option 1: Conda (Recommended)

```bash
# Clone repository
git clone https://github.com/shyu216/chinese-poetry-data-mining.git
cd chinese-poetry-data-mining

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate poetry-mining

# Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import node2vec; print(f'Node2Vec: {node2vec.__version__}')"
```

**Note:** The environment includes PyTorch CPU version by default. For GPU support, modify `environment.yml` to use `pytorch-gpu` channel.

### Option 2: pip

```bash
# Python 3.11+
git clone https://github.com/shyu216/chinese-poetry-data-mining.git
cd chinese-poetry-data-mining
pip install -r requirements.txt
```

### Generate Visualizations

```bash
# Make sure conda environment is activated
conda activate poetry-mining

# Option 1: Run all scripts sequentially
python scripts/03_generate_all.py

# Option 2: Run individual analysis scripts
python scripts/02_analysis_sentiment.py --data sample
python scripts/02_analysis_network.py --data sample --node2vec
python scripts/02_analysis_meter.py --data sample

# Option 3: Run individual visualization scripts
python scripts/03_vis_sentiment.py
python scripts/03_vis_network.py
python scripts/03_vis_dynasty.py
```

### View Results

```bash
# Start local server
python scripts/04_serve.py

# Or open directly
open reports/visualizations/index.html
```

### Run Tests

```bash
# Run comprehensive library tests
python scripts/test/test_all_libraries.py

# This tests:
# - Pandas/NumPy data processing
# - OpenCC/pypinyin text processing
# - Plotly visualization
# - scikit-learn TF-IDF and clustering
# - NetworkX social network analysis
# - gensim Word2Vec
```

## 📊 Live Demo

Visit our **[GitHub Pages](https://shyu216.github.io/chinese-poetry-data-mining)** for interactive visualizations!

![Sentiment Analysis](docs/assets/sentiment-preview.png)
*Example: Sentiment distribution across 331 classical poems*

## 📚 Documentation

- [Project Status](docs/PROJECT_STATUS.md) - Overall project progress and module completion
- [Daily Progress Summary](docs/2026-03-12-summary.md) - 2026-03-12 task progress and achievements
- [Development Progress](docs/2026-03-11-progress.md) - Initial development log
- [Refactoring Notes](docs/2026-03-11-refactor.md) - Code restructuring documentation
- [AI Development Guide](docs/AI_DEVELOPMENT_GUIDE.md) - Guide for AI assistants

## 📖 References

- [Text Mining Analysis of 50,000 Tang Poems (Tencent Cloud)](https://cloud.tencent.cn/developer/article/1541499) - Comprehensive NLP analysis of classical Chinese poetry
- [Ancient Poetry Dataset and NLP Applications (CSDN)](https://blog.csdn.net/weixin_36178216/article/details/151284411) - Dataset and practical NLP techniques for poetry analysis
- [Text Mining 540,000 Poems (Zhihu)](https://zhuanlan.zhihu.com/p/208751653) - Deep dive into poetry corpus analysis and insights

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - Comprehensive database of Chinese poetry in JSON format
- [ccpoems](https://github.com/shyu216/ccpoems) - React Native mobile app companion project

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <i>Exploring the beauty of Chinese poetry through data science 🏮</i>
</p>
