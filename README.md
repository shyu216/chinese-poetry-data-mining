# 🏮 Chinese Ancient Literature Atlas

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/Vue-3+-42b883.svg)](https://vuejs.org/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://shyu216.github.io/chinese-poetry-data-mining)

> Discover hidden temporal-spatial patterns and literary rules in classical Chinese poetry through data science

[中文版本](README.CN.md) · [Live Demo](https://shyu216.github.io/chinese-poetry-data-mining)

---

## ✨ Features

| Feature | Description |
|:---|:---|
| 🔍 **Full-text Search** | Cross-dynasty, cross-genre intelligent poetry search with multiple filters |
| 👤 **Poet Atlas** | Explore poet distribution by dynasty, understand the historical context of poetry's golden ages |
| 📊 **Word Frequency** | Analyze high-frequency words across different eras and writing preferences |
| ☁️ **Word Cloud** | Visualize poetry imagery with intuitive word clouds |
| 🔗 **Word Similarity** | Discover semantically related words using word embedding technology |
| 👥 **Poet Similarity** | Analyze poets' writing styles and find "like-minded" poets |
| 🎵 **Meter Analysis** | Parse poetry rhythm patterns and explore the beauty of classical Chinese versification |
| 📈 **Data Dashboard** | Overview of ancient literature data and overall distribution |

---

## 🚀 Quick Start

### Frontend Preview

```bash
# Clone the repository
git clone https://github.com/shyu216/chinese-poetry-data-mining.git

# Navigate to the web directory
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

### Production Build

```bash
# Build static files
npm run build

# Preview build output
npm run preview
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Vue 3 + Composition API
- **Language**: TypeScript
- **Build Tool**: Vite
- **Routing**: Vue Router
- **Visualization**: Plotly.js, D3.js

### Data Processing
- **Data Format**: FlatBuffers (High-performance binary serialization)
- **Chinese Processing**: jieba
- **Word Embedding**: FastText
- **Multiprocessing**: multiprocessing (Python)

### Deployment
- **Platform**: GitHub Pages
- **Approach**: Pure static deployment, no backend server required

---

## 📁 Project Structure

```
chinese-poetry-data-mining/
├── web/                      # Vue 3 frontend project
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── composables/      # Composables
│   │   ├── views/            # Page views
│   │   ├── generated/        # Generated type definitions
│   │   └── router/           # Router configuration
│   └── index.html
├── scripts/                  # Data processing scripts
│   ├── word_sim_v3.py        # Word similarity calculation
│   ├── author_sim_v2.py      # Poet similarity analysis
│   ├── wordcount_v2.py       # Word frequency statistics
│   └── flatbuffers_generated/# FlatBuffers schema
└── data/                     # Raw poetry data
    └── chinese-poetry/       # Ancient poetry database
        ├── 全唐诗/           # Complete Tang Poems
        ├── 宋词/             # Complete Song Ci
        ├── 元曲/             # Complete Yuan Qu
        └── 四书五经/         # Confucian Classics
```

---

## 📈 Data Scale

- **Complete Tang Poems**: 50,000+ poems
- **Song Ci**: 20,000+ poems
- **Yuan Qu**: Thousands of works
- **Four Books and Five Classics**: Complete collection

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit Issues and Pull Requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🙏 Acknowledgments

- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - Comprehensive database of Chinese poetry
- [ccpoems](https://github.com/shyu216/ccpoems) - React Native mobile app companion project

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <i>Rediscovering the beauty of classical Chinese poetry through data science 🏮</i>
</p>
