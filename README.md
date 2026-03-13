# Chinese Poetry Data Mining

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://shyu216.github.io/chinese-poetry-data-mining)

> 🏮 **Chinese Ancient Literature Atlas**: Static-site Data Mining over Classical Poems
>
> Discover hidden patterns in ancient Chinese literature through data science. **Pure static deployment, no backend required.**

[中文版本](README.CN.md) | [English Version](README.md)

---

## 🌟 Features

- **🔍 Full-text Search**: Client-side search across poems, authors, and dynasties
- **👥 Author Similarity**: Find poets with similar writing styles (TF-IDF + Cosine Similarity)
- **🕸️ Similarity Network**: Interactive D3.js visualization of poet relationships
- **📜 Meter Gallery**: Browse poems by meter patterns and verse forms
- **🏷️ POS Tagging**: Part-of-speech analysis of author writing styles
- **💡 Poetry Recommendation**: "Users who liked this also liked" recommendations
- **🚀 GitHub Pages Integration**: Auto-deploy to GitHub Pages (static only)

## 🏗️ Architecture

### Data Layer Architecture (Bronze/Silver/Gold)

```
RAW (原始) → BRONZE (清洗) → SILVER (结构化) → GOLD (分析) → OUTPUT (输出)
```

| Layer | Description | Format |
|-------|-------------|--------|
| **Bronze** | Cleaned and merged data | CSV + JSON metadata |
| **Silver** | Structured with meter extraction | CSV |
| **Gold** | Analysis results (similarity, word frequency) | JSON |
| **Output** | Web-ready static files | JSON chunks + HTML |

### Static Deployment

This project uses **pure static deployment**:

| Feature | Traditional | This Project |
|---------|-------------|--------------|
| Backend | Flask/Django server | ❌ None |
| Database | MySQL/PostgreSQL | ❌ None |
| Real-time compute | Server-side | ❌ None |
| Static files | HTML/CSS/JS | ✅ Yes |
| Client compute | Limited | ✅ Full JavaScript |

**How it works**:
1. **Build-time computation**: All analysis runs locally, generates static JSON indexes
2. **Static indexes**: Pre-computed search index, similarity matrix, recommendations
3. **Client-side search**: Pure JavaScript search using inverted index
4. **GitHub Pages**: Direct deployment of static files

## 🛠️ Tech Stack

| Category | Tools | Status |
|----------|-------|--------|
| Data Processing | Pandas, NumPy | ✅ Used |
| Text Processing | jieba, pypinyin, OpenCC | ✅ Used |
| Similarity | scikit-learn (TF-IDF, Cosine) | ✅ Used |
| Visualization | D3.js, Plotly | ✅ Used |
| Frontend | Vanilla JS, Web Workers | ✅ Used |
| **Removed** | | |
| Deep Learning | PyTorch, Transformers | ❌ Removed (not needed) |
| Network Analysis | NetworkX, Node2Vec | ❌ Removed (low accuracy) |
| Sentiment Analysis | Custom models | ❌ Removed (low accuracy) |

## 📁 Project Structure

```
chinese-poetry-data-mining/
├── data/
│   ├── bronze/                # Cleaned data (v1)
│   ├── silver/                # Structured data (v2)
│   ├── gold/                  # Analysis results (v3)
│   └── output/web/            # Web output (GitHub Pages)
├── src/
│   ├── analyzers/             # Analysis modules
│   ├── config/                # Configuration
│   └── schema/                # Data schemas
├── scripts/
│   ├── steps/                 # Data pipeline steps
│   │   ├── 01_clean.py
│   │   ├── 02_structure.py
│   │   ├── 03_analyze_words.py
│   │   └── 04_analyze_similarity.py
│   ├── index/                 # Index builders (static)
│   │   ├── build_search_index.py
│   │   ├── build_author_similarity_index.py
│   │   ├── build_word_similarity_index.py
│   │   ├── build_pos_index.py
│   │   ├── build_recommendation_index.py
│   │   └── build_all_indexes.py
│   └── export/                # Export scripts
│       └── web.py
├── docs/                      # Documentation
├── archive/legacy/            # Legacy code (archived)
└── .github/workflows/         # CI/CD (static deploy only)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip or conda

### Installation

```bash
# Clone repository
git clone https://github.com/shyu216/chinese-poetry-data-mining.git
cd chinese-poetry-data-mining

# Install dependencies
pip install -r requirements.txt
```

### Build Data Pipeline

```bash
# Run full data pipeline (one-time setup)
python scripts/steps/01_clean.py
python scripts/steps/02_structure.py
python scripts/steps/03_analyze_words.py
python scripts/steps/04_analyze_similarity.py

# Build all static indexes
python scripts/index/build_all_indexes.py

# Export web files
python scripts/export/web.py
```

### Local Development

```bash
# Start local server for testing
python -m http.server 8080 --directory data/output/web

# Or use the serve script
python scripts/export/web.py --serve
```

### View Results

Open http://localhost:8080 to view the static site locally.

## 📊 Live Demo

Visit our **[GitHub Pages](https://shyu216.github.io/chinese-poetry-data-mining)** for the live site!

**Features available**:
- 🔍 [Smart Search](https://shyu216.github.io/chinese-poetry-data-mining/search.html)
- 👥 [Author Similarity](https://shyu216.github.io/chinese-poetry-data-mining/author-similarity.html)
- 🕸️ [Similarity Network](https://shyu216.github.io/chinese-poetry-data-mining/similarity-network.html)
- 📜 [Meter Gallery](https://shyu216.github.io/chinese-poetry-data-mining/meter-gallery.html)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [2026-03-13-plan-refactor.md](docs/2026-03-13-plan-refactor.md) | Refactoring plan and architecture decisions |
| [2026-03-13-tasks-phase1.md](docs/2026-03-13-tasks-phase1.md) | Phase 1 tasks (data pipeline) |
| [2026-03-13-tasks-phase2.md](docs/2026-03-13-tasks-phase2.md) | Phase 2 tasks (static deployment) |
| [2026-03-13-report-index-build.md](docs/2026-03-13-report-index-build.txt) | Index build performance report |

## 🔄 Data Pipeline

```bash
# Full pipeline (run in order)
python scripts/steps/01_clean.py        # Bronze layer
python scripts/steps/02_structure.py     # Silver layer  
python scripts/steps/03_analyze_words.py # Word frequency
python scripts/steps/04_analyze_similarity.py # Similarity analysis

# Build static indexes
python scripts/index/build_all_indexes.py

# Export for web
python scripts/export/web.py
```

## 🏛️ Architecture Changes

### What's New (v1.0)

- ✅ **Pure static deployment** - No backend server needed
- ✅ **Client-side search** - Inverted index + Web Workers
- ✅ **Pre-computed indexes** - Similarity, recommendations built at build-time
- ✅ **Bronze/Silver/Gold layers** - Clear data lineage
- ✅ **D3.js visualizations** - Interactive network graphs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - Comprehensive database of Chinese poetry
- [ccpoems](https://github.com/shyu216/ccpoems) - React Native mobile app companion project

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <i>Exploring the beauty of Chinese poetry through data science 🏮</i>
</p>
