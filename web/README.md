# Web 前端优化说明

## 目标
本次对 `web/` 目录进行结构化优化，主要完成以下事项：

1. 为 `web/src` 下的 `.ts/.vue` 文件补充统一头部简介。
2. 在头部中补充技术栈、解决问题、数据源/数据流、复杂度说明。
3. 清理已确认未使用的前端文件与局部死代码。
4. 输出可持续维护的优化摘要文档。

## 头部规范
所有 `web/src` 下 `.ts/.vue` 文件已增加 `@overview` 头部，包含：

- `file`: 文件路径
- `category`: 文件类别（frontend/pipeline/algorithm/generated/types）
- `tech`: 主要技术
- `solved`: 该文件解决的问题
- `data_source`: 数据来源
- `data_flow`: 数据流转路径
- `complexity`: 时空复杂度或运行时开销概览

## 数据管线（Composables）概览
核心数据管线在 `web/src/composables`：

- 元数据与缓存：`useMetadataLoader.ts`, `useCacheV2.ts`, `useVerifiedCache.ts`
- 业务数据加载：`usePoemsV2.ts`, `useAuthorsV2.ts`, `useWordcountV2.ts`, `useWordSimilarityV2.ts`
- 检索索引：`useSearchIndexV2.ts`, `useKeywordIndex.ts`
- 分块加载与进度：`useChunkLoader.ts`, `useLoading.ts`

典型数据流：

`页面触发 -> composable 发起加载 -> 缓存校验/命中 -> 结果归一化 -> 响应式状态驱动组件渲染`

### 精读总结（数据管线）
- `usePoemsV2.ts`: 采用摘要/详情双缓存分层，支持按 `chunk_id` 快速路径回源，降低全量扫描概率。
- `useSearchIndexV2.ts`: 通过 `prefix` 分桶加载 poem_index，结合已加载前缀集合实现增量持久化。
- `useKeywordIndex.ts` / `useWordcountV2.ts`: 以分块+本地缓存为核心，优先热数据路径，提升首屏检索响应。

## 算法与复杂度概览
核心检索在 `web/src/search`：

- 缓存命中场景：常见 `O(1)`
- 线性筛选/匹配：常见 `O(n)`
- 分页截取：常见 `O(k)`（k 为页大小）
- 空间复杂度：通常 `O(n)`（索引与缓存大小相关）

### 精读总结（检索策略）
- `PoemSearch.ts`: 倒排索引 + 辅助索引 + LRU 组合，覆盖关键词命中与模糊回退。
- `AuthorSearch.ts` / `WordSearch.ts`: 面向热数据集合构建轻量索引，适合前端内存约束下的快速检索。
- 结果返回普遍采用“过滤 -> 评分/排序 -> 分页”流程，复杂度集中在 `O(n)` 与 `O(n log n)`。

## 前端页面与数据源概览
主要页面位于 `web/src/views`，数据来源以 `public/data` 及 composables 输出为主：

- `HomeView.vue`: 首页聚合展示
- `PoemsView.vue` / `PoemDetailView.vue`: 诗词列表与详情
- `AuthorsView.vue` / `AuthorDetailView.vue` / `ClusterDetailView.vue`: 诗人与聚类
- `WordCountView.vue`: 词频统计与词云
- `KeywordDetailView.vue`: 关键词分析与可视化
- `DataView.vue` 及其子页面：数据总览、下载、存储

### 精读总结（页面独特性）
- `AuthorsView.vue`: 具备“首批快速可交互 + 后台补齐”的分阶段加载体验。
- `AuthorClusterViz.vue`: 采用 Canvas 绘制 2D 聚类散点，支持悬停高亮与聚类筛选。
- `WordCountView.vue`: 结合统计卡片与词云可视化，展示词频分布与交互跳转。
- `DataDownload.vue`: 通过下载子模块聚合统一触发 `downloaded` 事件，便于上层页面协调状态。

## 已执行的清理

### 文件级清理
已删除明确未使用文件：

- `web/src/components/ui/transition/index.ts`
- `web/src/components/ui/transition/PageTransition.vue`
- `web/src/components/ui/virtual/index.ts`
- `web/src/components/ui/virtual/VirtualPoemList.vue`
- `web/src/composables/index.ts`
- `web/src/composables/useWorker.ts`
- `web/src/generated/author-chunk.ts`
- `web/src/generated/authorchunk.ts`
- `web/src/search/SearchManager.ts`
- `web/src/workers/dataProcessor.worker.ts`

### 代码级清理
- `web/src/components/data/DataDownload.vue`
  - 删除未使用 `ref` 定义与对应模板 `ref` 绑定
- `web/src/components/author/AuthorClusterViz.vue`
  - 删除未使用的 Naive UI / icon 导入
  - 删除未使用计算属性 `authorsByCluster`

## 剩余不可达项说明
当前剩余不可达主要是 `.d.ts` 类型声明文件：

- `web/src/types/d3-cloud.d.ts`
- `web/src/types/d3.d.ts`
- `web/src/types/plotly.d.ts`
- `web/src/types/vue-virtual-scroller.d.ts`

这类文件通常属于编译期类型兜底，建议在确认第三方类型来源后再决定是否删除。

## 建议
1. 在 CI 中增加 `vue-tsc --build` 与可选 lint 规则，持续约束未使用代码。
2. 后续新增文件时沿用 `@overview` 头部模板，保持文档化一致性。
3. 对 `types/*.d.ts` 做一次专项核查后再进行最小化清理。
