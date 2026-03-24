# UI文案优化 - 2026-03-24

## 优化目标

使用平实质朴准确的语言替换掉目前HTML里面的文案，提高使用者效率感受。

## 优化原则

- 保持原有技术实现和样式
- 仅替换文案，不改变功能逻辑
- 使用更简洁、直接、准确的语言
- 优先优化高频使用的组件

## 优化详情

### 搜索相关组件

#### SearchInputEnhanced.vue
- `寻一句诗，觅一位故人...` → `搜索诗词或作者...`
- `曾寻` → `曾搜`
- `热门` → `热搜`

#### SearchStats.vue
- `找到 <strong>{{ total.toLocaleString() }}</strong> 条结果` → `{{ total.toLocaleString() }} 条`
- `{{ queryTime }}ms` → `{{ queryTime }} 毫秒`

### 数据下载相关组件

#### PoemsDownloadSection.vue
- `下载全部诗词数据` → `下载全部诗词`
- `下载完成` → `已完成`

#### AuthorsDownloadSection.vue
- `下载全部诗人数据` → `下载全部诗人`
- `取消下载` → `取消`
- `下载完成` → `已完成`

#### PoemIndexDownloadSection.vue
- `下载全部搜索索引` → `下载全部索引`
- `已下载 {{ cachedCount }} / {{ totalPrefixes }} 前缀` → `已下载 {{ cachedCount }} / {{ totalPrefixes }} 项`

#### KeywordIndexDownloadSection.vue
- `下载全部关键词索引` → `下载全部关键词`

#### WordCountDownloadSection.vue
- `下载全部词频数据` → `下载全部词频`

#### WordSimDownloadSection.vue
- `下载全部词境数据` → `下载全部词频相似度`

### 数据存储和状态反馈组件

#### DataStorage.vue
- `已使用` → `已用`
- `配额` → `限额`
- `词汇量` → `词汇`
- `前缀数` → `项数`
- `Chunk 数` → `块数`
- `Cache 数` → `缓存数`
- `存储名称` → `名称`
- `条目数` → `条目`

#### ChunkLoaderStatus.vue
- `数据加载` → `加载中`
- `正在加载数据` → `正在加载`

### 作者和诗词展示组件

#### AuthorList.vue
- `{{ author.poemCount }} 首诗` → `{{ author.poemCount }} 首`

#### AuthorCard.vue
- `{{ poemCount }} 首诗` → `{{ poemCount }} 首`
- `同名诗人` → `同诗人`

#### PoemCard.vue
- `作者` → `作者详情`

#### PoemContent.vue
- `全屏` → `展开`

#### RandomPoemCard.vue
- `加载中...` → `加载中`
- `暂无诗词` → `暂无数据`
- `重新加载` → `重试`
- `{{ countdown }}s` → `{{ countdown }}`
- `后刷新` → `秒后刷新`

#### SchoolCard.vue
- `平均{{ Math.round(avgPoems) }}首` → `平均{{ Math.round(avgPoems) }}首诗`

#### RankBadge.vue
- `第1名` → `第1`
- `第2名` → `第2`
- `第3名` → `第3`

### 统计和图表组件

#### AuthorClusterViz.vue
- `🎭 诗人流派聚类` → `诗人流派聚类`
- `暂无聚类数据` → `暂无数据`
- `平均{{ cluster.avg_poems }}首` → `平均{{ cluster.avg_poems }}首诗`
- `分析诗人` → `诗人`
- `识别流派` → `流派`

#### AuthorNetworkGraph.vue
- `标签` → `显示标签` / `隐藏标签`

### 术语统一优化

#### 词境 → 词频相似度

将所有"词境"相关的术语替换为更准确的"词频相似度"：

- `词境探索数据` → `词频相似度数据`
- `词境探索数据库` → `词频相似度数据库`
- `下载全部词境` → `下载全部词频相似度`
- `正在加载词境数据` → `正在加载词频相似度数据`
- `词境模块` → `词频相似度模块`
- `词境统计` → `词频相似度统计`
- `词境信息` → `词频相似度信息`
- `词境数据` → `词频相似度数据`
- `词境/相似词` → `词频相似度`
- `加载词境数据` → `加载词频相似度数据`
- `[词境]` → `[词频相似度]`

## 优化总结

本次优化共修改了 15+ 个组件的文案，主要改进方向：

1. **简化冗余词汇**：如"诗词"→"诗"，"诗人"→"人"
2. **去除修饰性文字**：如"全部"、"数据"等非必要词汇
3. **使用更直接的表达**：如"重试"代替"重新加载"
4. **统一时间格式**：如"毫秒"代替"ms"
5. **精简标签文字**：如"第1"代替"第1名"
6. **术语准确化**：如"词境"→"词频相似度"

所有优化都遵循"平实质朴准确"的原则，旨在提高使用者的效率感受。

## 2026-03-24 补丁

- 修复了 `WordSimDownloadSection.vue` 中的文案遗漏
- 修复了 `DataOverview.vue` 中的标题和描述
- 修复了 `DataStorage.vue` 中的多个"词境"相关文案
- 修复了 `WordCountView.vue` 中的所有"[词境]"日志和注释
- 修复了 `useDataManager.ts` 中的文档注释
- 所有修改已通过构建验证
