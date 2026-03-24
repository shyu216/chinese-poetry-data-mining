# 中华诗词库 - Web 应用

基于 chinese-poetry 开源数据库构建的现代化中文诗词数据挖掘与可视化平台，收录了超过30万首来自多个朝代的诗词。

## 功能特性

### 诗词浏览
- 浏览全量诗词数据（30万+首）
- 按朝代、体裁筛选
- 搜索诗词标题与作者
- 随机排序与换一批
- 诗词详情页展示

### 诗人名录
- 按诗词数量排序
- 搜索诗人姓名
- 诗人作品集展示
- 诗人流派聚类
- 相似诗人推荐

### 词频分析
- 词汇频率统计
- 词境相似度分析
- 词云可视化
- 词汇筛选与搜索
- 关键词检索

### 数据管理
- 数据总览统计
- 数据下载（CSV/JSON）
- 索引文件下载
- 缓存管理
- 存储空间分析

## 技术栈

### 核心框架
- Vue 3.5.29 - 组合式 API
- TypeScript 5.9.3 - 类型安全
- Vite 7.3.1 - 构建工具
- Vue Router 4.6.4 - 路由管理

### UI 组件
- Naive UI 2.44.1 - 桌面端 UI 组件库
- Vicons Ionicons5 - 图标库

### 数据可视化
- D3.js 7.9.0 - 数据驱动图表
- D3-Cloud - 词云布局
- Plotly.js - 交互式图表

### 状态管理
- Composables 模式 - 组合式函数
- IDB (IndexedDB) - 客户端数据库
- LRU 缓存 - 搜索结果缓存

## 快速开始

### 环境要求
- Node.js: ^20.19.0 || >=22.12.0
- npm / pnpm / yarn

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 生产构建
```bash
# 类型检查 + 构建
npm run build

# 仅构建
npm run build-only

# 构建并生成哈希manifest
npm run build:with-hash
```

### 预览构建
```bash
npm run preview
```

## 项目结构

```
web/
├── src/
│   ├── components/          # 组件库
│   │   ├── content/        # 内容展示
│   │   ├── author/         # 诗人相关
│   │   ├── display/        # 数据可视化
│   │   ├── search/         # 搜索功能
│   │   ├── ui/             # UI 基础组件
│   │   └── feedback/       # 加载反馈
│   ├── composables/        # 组合式函数
│   ├── search/             # 搜索模块
│   ├── views/              # 页面视图
│   ├── router/             # 路由配置
│   └── types/              # 类型定义
├── public/                 # 静态资源
└── data/                   # 数据文件（需从主仓库同步）
```

## 数据结构

### 诗词数据 (poems-summary-v2)
```typescript
interface PoemSummary {
  id: string              // 诗词ID
  title: string           // 标题
  author: string          // 作者
  dynasty: string         // 朝代 (唐/宋/元/明/清)
  genre: string           // 体裁 (诗/词)
  chunk_id?: number       // 所在分块ID
}
```

### 诗词详情 (poems-detail-v2)
```typescript
interface PoemDetail extends PoemSummary {
  poem_type?: string      // 诗体
  meter_pattern?: string  // 平仄格律
  sentences: string[]     // 句子数组
  words: string[]         // 词汇数组
  hash: string            // 数据哈希
}
```

### 诗人数据 (authors-v2)
```typescript
interface AuthorStats {
  author: string                      // 诗人姓名
  poem_count: number                  // 诗词数量
  poem_ids: string[]                  // 诗词ID列表
  poem_type_counts: Record<string, number>  // 诗体分布
  meter_patterns: Array<{            // 平仄模式
    pattern: string
    count: number
  }>
  word_frequency: Record<string, number>      // 词汇频率
  similar_authors: Array<{           // 相似诗人
    author: string
    similarity: number
  }>
}
```

### 词频数据 (wordcount-v2)
```typescript
interface WordCountItem {
  word: string    // 词汇
  count: number   // 出现次数
  rank: number    // 排名
}
```

## 搜索系统

### 倒排索引
- 关键词 → 诗词ID 映射
- O(1) 时间复杂度查找
- 支持多条件过滤

### 搜索功能
```typescript
// 诗词搜索
searchPoems(query, { dynasty, genre })

// 作者搜索
searchAuthors(query)

// 词汇搜索
searchWords(query)
```

## 缓存策略

### 分层缓存
1. 内存缓存 - Composables 层
2. LRU 缓存 - 搜索结果
3. IndexedDB - 持久化存储
4. Chunk 分块 - 按需加载

### 缓存键名
- poems-summary-v2 - 诗词摘要
- poems-detail-v2 - 诗词详情
- authors-v2 - 诗人数据
- wordcount-v2 - 词频数据
- word-similarity-v2 - 词境相似度

## 性能优化

1. 懒加载 - 路由组件按需加载
2. 代码分割 - Vite 自动代码分割
3. CDN 加载 - 外部依赖 CDN
4. Worker 线程 - 数据处理后台化
5. 虚拟滚动 - 大列表优化
6. 批量加载 - Chunk 批量获取

## 数据来源

本项目数据基于以下开源项目：

- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - 中文诗词开源数据库
- [chinese-poetry-data-mining](https://github.com/chinese-poetry/chinese-poetry-data-mining) - 数据挖掘项目

## 许可证

本项目遵循 MIT License。

## 致谢

感谢以下开源项目的贡献：

- [Vue.js](https://vuejs.org/)
- [Naive UI](https://www.naiveui.com/)
- [D3.js](https://d3js.org/)
- [IDB](https://github.com/jakearchibald/idb)
