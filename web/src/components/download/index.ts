/**
 * 文件: web/src/components/download/index.ts
 * 说明: 导出数据下载相关的 UI 区块组件（诗文、作者、词频、相似度、索引）。
 *
 * 数据管线:
 *   - 这些组件通常提供对后端/静态文件的下载入口，或生成并链接预先生成的数据包（如 JSON/CSV/压缩包）。
 *   - 可触发后端导出任务或直接返回静态资源 URL。
 *
 * 复杂度:
 *   - UI 层为常数复杂度 O(1)，生成/打包操作的成本取决于后端实现或客户端打包逻辑（可能为 O(n)）。
 *
 * 注意:
 *   - 大文件下载需支持分块/断点续传与后台任务状态查询，以免阻塞前端或导致超时。
 */
export { default as PoemsDownloadSection } from './PoemsDownloadSection.vue'
export { default as AuthorsDownloadSection } from './AuthorsDownloadSection.vue'
export { default as WordCountDownloadSection } from './WordCountDownloadSection.vue'
export { default as PoemIndexDownloadSection } from './PoemIndexDownloadSection.vue'
export { default as KeywordIndexDownloadSection } from './KeywordIndexDownloadSection.vue'
