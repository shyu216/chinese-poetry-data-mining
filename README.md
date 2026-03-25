# Chinese Poetry Data Mining

A modern, data-driven exploration of classical Chinese poetry with over 300,000 poems from multiple dynasties.

## Key Features

- **Extensive Poetry Collection**: Access 300,000+ poems from Tang, Song, Yuan, Ming, and Qing dynasties
- **Advanced Search**: Full-text search with inverted index for instant results
- **Poet Analysis**: Explore 5,000+ poets with style similarity analysis and clustering
- **Word Frequency Analysis**: Discover high-frequency words and semantic relationships
- **Data Visualization**: Interactive word clouds and poet network graphs
- **Responsive Design**: Mobile-friendly interface with smooth animations

### Production Build

```bash
# Build static files
npm run build

# Preview build output
npm run preview
```

## Data Scale

- **Total Poems**: 300,000+
  - Tang Poems: 50,000+
  - Song Poems: 200,000+
  - Song Ci: 20,000+
- **Total Poets**: 5,000+
- **Word Statistics**: 1,000,000+
- **Data Structure**: Optimized with FlatBuffers for performance

## Project Structure

```
chinese-poetry-data-mining/
├── web/              # Vue 3 frontend application
├── scripts/          # Data processing and analysis scripts
└── data/             # Raw poetry data
```

## Technology Stack

- **Frontend**: Vue 3, TypeScript, Vite, Naive UI, D3.js
- **Data Processing**: Python, jieba, FastText, FlatBuffers
- **Deployment**: GitHub Pages (static site)

## Usage Guide

### Browsing Poems
- Filter by dynasty and genre
- Search by title and author
- View detailed poem information including meter patterns

### Exploring Poets
- Sort poets by poem count
- View poet collections and style analysis
- Discover similar poets based on writing style

### Analyzing Words
- Explore word frequency across different eras
- Visualize word relationships with word clouds
- Search for specific keywords and their context

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Data Sources

This project is based on the [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) open-source database.

## Acknowledgments

- [Vue.js](https://vuejs.org/) - Progressive JavaScript framework
- [Naive UI](https://www.naiveui.com/) - Vue 3 component library
- [D3.js](https://d3js.org/) - Data visualization library
- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - Poetry database

## Live Demo

[https://shyu216.github.io/chinese-poetry-data-mining](https://shyu216.github.io/chinese-poetry-data-mining)
