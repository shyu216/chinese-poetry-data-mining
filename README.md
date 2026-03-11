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

| Category | Tools |
|----------|-------|
| Data Processing | Pandas, NumPy |
| Text Processing | OpenCC (Traditional/Simplified), pypinyin |
| Feature Extraction | Custom rhyme, sentiment, semantic extractors |
| Visualization | Plotly, Pyecharts, Dash |
| Machine Learning | scikit-learn (TF-IDF, similarity, clustering) |
| Network Analysis | NetworkX |

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
│   └── serve_visualizations.py # Local server
├── reports/
│   └── visualizations/        # Generated HTML visualizations
├── docs/                      # Documentation
└── .github/workflows/         # CI/CD for GitHub Pages
```

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+
git clone https://github.com/shyu216/chinese-poetry-data-mining.git
cd chinese-poetry-data-mining
pip install -r requirements.txt
```

### Generate Visualizations

```bash
# Option 1: Run all scripts sequentially
python scripts/generate_all_visualizations.py

# Option 2: Run individual scripts
python scripts/03_vis_sentiment.py
python scripts/03_vis_network.py
python scripts/03_vis_dynasty.py
```

### View Results

```bash
# Start local server
python scripts/serve_visualizations.py

# Or open directly
open reports/visualizations/index.html
```

## 📊 Live Demo

Visit our **[GitHub Pages](https://shyu216.github.io/chinese-poetry-data-mining)** for interactive visualizations!

![Sentiment Analysis](docs/assets/sentiment-preview.png)
*Example: Sentiment distribution across 331 classical poems*

## 📚 Documentation

- [Development Progress](docs/2026-03-11-progress.md) - Initial development log
- [Refactoring Notes](docs/2026-03-11-refactor.md) - Code restructuring documentation

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
