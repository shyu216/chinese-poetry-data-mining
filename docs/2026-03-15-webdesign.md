# 前端静态展示 Web 设计方案

## 📋 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | **Vue 3 + Vite** | 组件化开发，体验好 |
| UI 库 | **Naive UI** 或 **Tailwind CSS** | 统一样式，快速开发 |
| 可视化 | **Plotly.js** + **D3.js** | Plotly 统计图，D3 网络图 |
| 构建工具 | **Vite** | 快如闪电，自动打包 |
| 数据处理 | **Python** | 构建时生成静态索引 |
| 部署 | **GitHub Pages** | 免费静态托管 |

## 📊 当前数据状态分析

### results 目录结构

| 目录 | 文件数 | 数据格式 | 用途 |
|------|--------|----------|------|
| `preprocessed/` | 333 个 CSV | id, title, author, dynasty, genre, sentences_simplified, meter_pattern, hash, words | 清洗后的诗词数据 |
| `keyword_index/` | 2927 个 JSON | keyword → [poem_id, ...] | 关键词到 ID 的映射 |
| `ngram_index/` | 999+ 个 JSON | ngram → [poem_id, ...] | N-gram 索引 |
| `fasttext/` | 模型文件 | 二进制模型 | 词向量（100维） |
| `wordcount/` | 1 个 CSV | word, frequency | 全局词频统计 |

### 数据规模

- 诗词总数：约 33 万首
- 关键词数量：约 11.5 万个
- N-gram 总数：1-gram: 89万, 2-gram: 728万, 3-gram: 1020万

## ⚠️ 当前问题：无法直接支持低延迟渲染

### 问题 1：数据分散，缺少整合

- `keyword_index` 只映射关键词 → 诗歌 ID
- `preprocessed` 包含诗歌内容，但需要通过 ID 查找
- 客户端无法高效执行 "关键词搜索 + 内容返回"

### 问题 2：缺少元数据索引

原项目有 `author_index.json`、`dynasty_index.json`，但新数据没有对应文件

### 问题 3：FastText 模型无法浏览器加载

- `fasttext/` 模型是二进制格式
- 浏览器无法直接使用，需要 WebAssembly 或后端 API

### 问题 4：文件碎片化

- 2927 个 keyword JSON 文件
- 333 个 poem CSV 分片
- HTTP 请求数过多，首屏加载慢

## ✅ 解决方案：构建中间索引文件

### 方案：生成 Web 就绪的静态索引

需要构建一个新的索引层，输出到 `data/web/`：

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
└── src/
    ├── components/
    │   ├── Navbar.vue            # 导航栏
    │   ├── Footer.vue            # 页脚
    │   ├── PoemCard.vue          # 诗歌卡片
    │   ├── PoemModal.vue         # 诗歌详情弹窗
    │   └── Loading.vue           # 加载组件
    ├── views/
    │   ├── HomeView.vue          # 首页/搜索
    │   ├── PoetsView.vue         # 诗歌浏览
    │   ├── AuthorsView.vue       # 作者页
    │   ├── StatsView.vue         # 统计仪表板
    │   └── WordcloudView.vue     # 词云展示
    ├── composables/
    │   ├── useSearchIndex.js     # 搜索索引加载
    │   ├── usePoems.js           # 诗歌数据
    │   └── useAuthors.js         # 作者数据
    ├── App.vue
    └── main.js
```

### 索引设计

#### 1. search_index.json（倒排索引）

```json
{
  "metadata": {
    "version": "v1",
    "total_poems": 332509,
    "total_keywords": 115255,
    "build_time": "2026-03-15T12:00:00"
  },
  "index": {
    "春风": [
      {"id": "xxx", "title": "春晓", "author": "孟浩然", "dynasty": "唐", "score": 5},
      {"id": "yyy", "title": "咏柳", "author": "贺知章", "dynasty": "唐", "score": 3}
    ],
    "明月": [
      {"id": "aaa", "title": "静夜思", "author": "李白", "dynasty": "唐", "score": 5}
    ]
  }
}
```

**设计原则**：
- 每个关键词最多返回 Top 20 条结果
- 包含诗歌 ID、标题、作者、朝代
- 不包含完整诗歌内容（减少体积）
- 按首字母分片加载，减少首屏请求

#### 2. author_index.json（作者索引）

```json
{
  "metadata": {
    "total_authors": 15000
  },
  "authors": {
    "李白": {
      "dynasty": "唐",
      "poem_count": 1100,
      "genres": ["诗", "词"],
      "poem_ids": ["id1", "id2", ...]
    }
  }
}
```

#### 3. poems/summary.json（诗歌摘要）

```json
{
  "metadata": {
    "total": 332509,
    "chunks": 34,
    "chunk_size": 10000
  },
  "poems": [
    {
      "id": "xxx",
      "title": "春晓",
      "author": "孟浩然",
      "dynasty": "唐",
      "genre": "诗",
      "poem_type": "五言绝句",
      "meter_pattern": "5,5,5,5"
    }
  ]
}
```

## 🎨 前端页面设计

### 页面 1：首页/搜索 (HomeView.vue)

**功能**：
- 关键词搜索（支持多关键词 AND/OR）
- 搜索结果实时显示（虚拟滚动）
- 点击结果展示诗歌详情弹窗
- 按作者/朝代/体裁筛选

**技术**：
- 加载 search_index.json（分片加载，按需加载）
- 虚拟滚动（最多渲染 100 条）
- 搜索结果缓存

### 页面 2：诗歌浏览 (PoetsView.vue)

**功能**：
- 分页浏览所有诗歌
- 按朝代/体裁/作者筛选
- 诗歌详情（点击展开完整内容）

**技术**：
- 分片加载 poems/summary.json
- 按需加载诗歌详情

### 页面 3：作者主页 (AuthorsView.vue)

**功能**：
- 作者列表（按诗歌数量排序）
- 作者详情页（展示该作者所有诗歌）
- 作者相似度（基于词频预计算）

**技术**：
- 加载 author_index.json

### 页面 4：统计仪表板 (StatsView.vue)

**功能**：
- 诗词数量统计（按朝代/体裁）
- 格律分布图
- 高频词汇排行

**技术**：
- 加载 metadata.json
- Plotly.js 柱状图、饼图

### 页面 5：词云展示 (WordcloudView.vue)

**功能**：
- 全局词云
- 按朝代/作者的词云对比
- 词频统计表

**技术**：
- 加载 wordfreq.json
- D3.js 词云布局

## 🚀 实施步骤

### 步骤 1：创建 Vue 3 项目

```bash
# 使用 Vite 创建项目
npm create vite@latest poetry-web -- --template vue

# 进入项目目录
cd poetry-web

# 安装依赖
npm install

# 安装 UI 库（选择其一）
npm install naive-ui        # 或
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 安装可视化库
npm install plotly.js-dist-min d3

# 运行开发服务器
npm run dev
```

### 步骤 2：构建中间索引（Python）

```python
# scripts/build_web_index.py
def build_search_index():
    # 1. 加载 keyword_index 和 preprocessed
    # 2. 合并为完整的倒排索引
    # 3. 限制每个关键词返回 Top 20 结果
    # 4. 按首字母分片输出为 JSON

def build_author_index():
    # 按作者聚合诗歌

def build_poem_summary():
    # 生成诗歌摘要列表
```

### 步骤 3：数据分片策略

- **搜索索引**：按首字母分片（a.json, b.json, ...），约 26 个文件
- **诗歌摘要**：按 10000 首分片，约 34 个文件
- **作者索引**：单个文件（约 5-10MB）

### 步骤 4：前端开发

- 使用 Vue 3 组件化开发
- 实现虚拟滚动
- 实现分片加载
- 实现搜索缓存
- Plotly + D3 可视化

## 📈 预期性能

| 指标 | 目标 |
|------|------|
| 首屏加载 | < 3s |
| 搜索响应 | < 100ms |
| 内存占用 | < 200MB |
| 索引文件总大小 | 100-200MB |

## 🔄 部署流程

```bash
# 1. 构建 Web 索引
python scripts/build_web_index.py

# 2. 复制索引到 Vue 项目的 public 目录
cp -r data/web/* poetry-web/public/

# 3. 构建生产版本
npm run build

# 4. 部署到 GitHub Pages
# 方法 A: 使用 gh-pages
npm install -D gh-pages
npm run build && gh-pages -d dist

# 方法 B: Vercel 一键部署
# 将项目推送到 GitHub，Vercel 自动识别 Vue 项目
```

## ⚠️ 注意事项

1. **FastText 词向量**：如需作者相似度/词向量搜索，在构建时预计算为 JSON
2. **数据更新**：每次数据更新后需重新构建索引
3. **GitHub Pages**：项目需设为 public 或使用 private + Vercel

## 📦 项目文件结构（最终）

```
chinese-poetry-data-mining/
├── results/                    # 原始分析结果 (3.5GB)
├── data/
│   └── web/                   # Web 索引 (200MB)
│       ├── index/
│       ├── poems/
│       └── assets/
├── poetry-web/                # Vue 3 前端项目
│   ├── public/                # 静态资源（索引 JSON）
│   ├── src/
│   │   ├── components/        # Vue 组件
│   │   ├── views/             # 页面视图
│   │   ├── composables/       # 组合式函数
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.js
└── docs/
    └── webdesign.md           # 本文档
```
