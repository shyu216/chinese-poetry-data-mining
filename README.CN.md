# 中华诗词数据挖掘

一个现代化、数据驱动的古典诗词探索平台，收录了超过30万首来自多个朝代的诗词。

## 核心功能

- **丰富的诗词收藏**：访问30万+首唐诗、宋词、元曲等多个朝代的诗词
- **高级搜索**：全文检索，使用倒排索引实现即时搜索结果
- **诗人分析**：探索5,000+位诗人，包括风格相似度分析和聚类
- **词频分析**：发现高频词汇和语义关系
- **数据可视化**：交互式词云和诗人网络图
- **响应式设计**：移动友好的界面，流畅的动画效果

## 数据规模

- **诗词总数**：300,000+首
  - 唐诗：50,000+首
  - 宋诗：200,000+首
  - 宋词：20,000+首
- **诗人数量**：5,000+位
- **词汇统计**：1,000,000+条
- **数据结构**：使用FlatBuffers优化性能

## 项目结构

```
chinese-poetry-data-mining/
├── web/              # Vue 3前端应用
├── scripts/          # 数据处理和分析脚本
└── data/             # 原始诗词数据
```

## 技术栈

- **前端**：Vue 3, TypeScript, Vite, Naive UI, D3.js
- **数据处理**：Python, jieba, FastText, FlatBuffers
- **部署**：GitHub Pages（静态站点）

## 使用指南

### 浏览诗词
- 按朝代和体裁筛选
- 按标题和作者搜索
- 查看详细的诗词信息，包括格律模式

### 探索诗人
- 按诗词数量排序诗人
- 查看诗人作品集和风格分析
- 基于写作风格发现相似诗人

### 分析词汇
- 探索不同时代的词汇频率
- 使用词云可视化词汇关系
- 搜索特定关键词及其上下文

## 许可证

MIT许可证 - 详见 [LICENSE](LICENSE) 文件。

## 数据来源

本项目基于 [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 开源数据库。

## 致谢

- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Naive UI](https://www.naiveui.com/) - Vue 3组件库
- [D3.js](https://d3js.org/) - 数据可视化库
- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) - 诗词数据库

## 在线演示

[https://shyu216.github.io/chinese-poetry-data-mining](https://shyu216.github.io/chinese-poetry-data-mining)

