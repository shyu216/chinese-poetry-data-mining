# 词频相似度模块移除

**日期**: 2026-04-07

**任务**: 移除 word_similarity_v3 相关功能

## 完成的操作

### 1. Git 缓存和忽略配置
- 从 git 缓存移除 `results/word_similarity_v3/` 目录
- 将 `results/word_similarity_v3/` 添加到 `.gitignore`

### 2. Composable 函数删除
- 删除 `web/src/composables/useWordSimilarityV2.ts`
- 从 `useMetadataLoader.ts` 移除 `useWordSimilarityMetadata` 和 `WORD_SIMILARITY_STORAGE`

### 3. 前端组件和逻辑删除

**Views**:
- `HomeView.vue` - 移除词频相似度统计卡片和数据加载
- `WordCountView.vue` - 移除相似词展示功能

**Components**:
- `DataOverview.vue` - 移除词频相似度统计展示
- `DataStorage.vue` - 移除存储管理和缓存清理
- `DataDownload.vue` - 移除 WordSimDownloadSection
- `download/index.ts` - 移除导出
- `WordSimDownloadSection.vue` - 删除整个文件

**Composables**:
- `useChunkLoader.ts` - 移除 wordcountWordSim 配置键

### 4. 代码清理
- 更新相关文件的注释说明
- Build 验证通过，无报错

### 5. 补充：首页词汇卡片
- 在 `HomeView.vue` 添加词汇统计卡片
- 使用 `useWordcountV2` 的 `totalWords` 展示总词汇数
- Build 验证通过，无报错
