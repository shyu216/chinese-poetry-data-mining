# 2026-03-15 前端静态展示方案

## 核心问题

数据分散，缺少整合，无法直接支持低延迟渲染。

## 解决方案：构建中间索引

```
data/web/
├── index/
│   ├── search_index.json      # 倒排索引
│   ├── author_index.json      # 作者索引
│   ├── dynasty_index.json     # 朝代索引
│   └── metadata.json          # 全局统计
├── poems/
│   ├── summary.json           # 诗歌摘要
│   └── chunks/                # 详情分片
└── assets/
    └── wordfreq.json          # 词频统计
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + Vite |
| UI库 | Naive UI / Tailwind CSS |
| 可视化 | Plotly.js + D3.js |
| 部署 | GitHub Pages |

## 数据规模

- 诗词总数：约33万首
- 关键词数量：约11.5万个
- N-gram总数：1-gram 89万, 2-gram 728万, 3-gram 1020万

## 关键创新

纯静态架构：构建时计算所有分析，客户端只执行查询。
