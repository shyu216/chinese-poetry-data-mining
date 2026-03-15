# GitHub Actions 部署方案

> 记录项目部署到 GitHub Pages 的完整方案  
> **最后更新**: 2026-03-15

---

## 📋 部署架构

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | **Vue 3 + Vite** | 组件化开发 |
| UI 库 | **Naive UI** + **Tailwind CSS** | 统一样式 |
| 可视化 | **Plotly.js** + **D3.js** | 统计图 + 网络图 |
| 构建工具 | **Vite** | 自动打包 |
| 部署 | **GitHub Pages** | 免费静态托管 |

---

## 🔄 工作流设计

### 触发条件优化

```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'web/**'
      - 'results/**'
      - '.github/workflows/deploy-pages.yml'
  workflow_dispatch:
```

**优化点**: 使用 `paths` 过滤，只在相关文件变更时触发部署。

### 并发控制

```yaml
concurrency:
  group: 'pages'
  cancel-in-progress: true
```

**优化点**: 防止多个部署同时运行，节省 GitHub Actions 运行时间。

---

## 💻 跨平台软连接解决方案

### 问题背景

- Windows 本地开发使用 `mklink` 创建软连接：`web\public\data` → `results`
- GitHub Actions 运行在 Ubuntu 上，软连接可能无法正确解析
- Git 对软连接的处理在不同平台上有差异

### 解决方案：构建时复制

```yaml
- name: Setup data directory (cross-platform symlink workaround)
  run: |
    mkdir -p web/public/data
    cp -r results/author web/public/data/
    cp -r results/preprocessed web/public/data/
    cp -r results/wordcount web/public/data/
```

**优点**:
- 完全跨平台兼容
- 可以选择性复制必要数据，减少部署体积
- 不依赖 Git 的软连接支持

---

## 📊 数据体积分析

### 当前数据分布

| 目录 | 大小 | 文件数 | 用途 | 部署状态 |
|------|------|--------|------|----------|
| `results/author/` | ~52 MB | ~857 个 | 作者统计信息 | ✅ 部署 |
| `results/preprocessed/` | ~243 MB | 333 个 | 诗词预处理数据 | ✅ 部署 |
| `results/wordcount/` | ~16 MB | 多个 | 词频统计 | ✅ 部署 |
| `results/word_similarity_v2/` | ~1.8 GB | ~231 个 | 词相似度计算 | ❌ 排除 |
| **部署总计** | **~311 MB** | - | - | - |

### 部署策略

当前工作流只复制**约 311 MB** 的必要数据，排除了 word_similarity_v2 (1.8 GB) 等大数据集。

---

## 🚀 大数据部署方案对比

针对 `word_similarity_v2` (~1.8GB) 的部署选项：

| 方案 | 复杂度 | 成本 | 部署体积 | 访问速度 | 维护难度 |
|------|--------|------|----------|----------|----------|
| **A. Git LFS + Release** | 低 | 免费 | ~500MB (压缩后) | 中等 | 低 |
| **B. 外部 CDN (R2/S3)** | 中 | 免费额度 | 1.8GB | 快 | 中 |
| **C. 数据压缩 + 按需加载** | 高 | 免费 | ~400MB | 中等 | 高 |
| **D. 分仓库部署** | 中 | 免费 | 1.8GB | 中等 | 中 |
| **E. 功能降级/采样** | 低 | 免费 | ~100MB | 快 | 低 |

### 推荐方案

**短期**: 使用方案 E（功能降级），仅部署高频词的相似度数据  
**长期**: 考虑方案 B（外部 CDN），获得更好的访问速度

---

## 🏗️ Web 数据索引设计

### 索引结构

```
data/web/
├── public/
│   ├── index/
│   │   ├── search_index.json      # 倒排索引（分片）
│   │   ├── author_index.json      # 作者索引
│   │   ├── dynasty_index.json     # 朝代索引
│   │   ├── genre_index.json      # 体裁索引
│   │   └── metadata.json         # 全局统计信息
│   ├── poems/
│   │   ├── summary.json          # 诗歌摘要列表
│   │   └── chunks/               # 诗歌详情分片
│   └── assets/
│       ├── wordfreq.json         # 词频统计
│       └── ngram_stats.json      # N-gram 统计
```

### 渐进式加载策略

**问题**: 33万首诗词无法一次性加载  
**方案**: 将数据分成 333 个 chunks，每 chunk 约 1000 首

```
初始加载: 1 chunk (~1000首)
用户翻页: 从已加载 chunks 中筛选分页
到达末页: 自动加载下一 chunk
手动加载: 点击"加载更多"按钮
```

---

## 💾 IndexedDB 缓存架构

### 存储结构

```
IndexedDB: poem-cache
├── chunks (ObjectStore)          # 分块摘要数据
│   └── { id, poems[], timestamp }
├── chunkDetails (ObjectStore)    # 诗词详情数据
│   └── { id, poems: Map, timestamp }
├── index (ObjectStore)           # 索引数据
│   └── { key: 'main', data, timestamp }
└── metadata (ObjectStore)        # 会话元数据
    └── { key: 'session', loadedChunkIds[], timestamp }
```

### 数据流

```
首次访问:
  加载 index.json → 缓存到 IndexedDB
  加载 chunk 0 → 缓存到 IndexedDB
  记录 loadedChunkIds → 缓存到 IndexedDB

刷新页面:
  从 IndexedDB 读取 index
  从 IndexedDB 读取 loadedChunkIds
  从 IndexedDB 恢复已加载的 chunks
  无需网络请求，立即显示
```

---

## 📦 完整工作流示例

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'web/**'
      - 'results/**'
      - '.github/workflows/deploy-pages.yml'
  workflow_dispatch:

concurrency:
  group: 'pages'
  cancel-in-progress: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup data directory
        run: |
          mkdir -p web/public/data
          cp -r results/author web/public/data/
          cp -r results/preprocessed web/public/data/
          cp -r results/wordcount web/public/data/

      - name: Install dependencies
        run: cd web && npm ci

      - name: Build
        run: cd web && npm run build

      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
        with:
          folder: web/dist
```

---

## 🔧 进一步优化建议

### 短期优化

1. **启用 Gzip 压缩**
   - 服务器端启用 gzip
   - 预计减少 60-70% 传输体积

2. **实施懒加载策略**
   - 首屏只加载必要数据
   - 路由级代码分割

3. **图片优化**
   - 使用 WebP 格式
   - 实现懒加载

### 长期优化

1. **Service Worker 缓存**
   - 离线访问支持
   - 智能缓存策略

2. **CDN 加速**
   - 静态资源托管到 CDN
   - 全球加速访问

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [00-project-guide.md](./00-project-guide.md) | 项目开发指南 |
| [01-web-design.md](./01-web-design.md) | Web 创意设计方案 |
| [02-data-pipeline.md](./02-data-pipeline.md) | 数据处理管线 |
