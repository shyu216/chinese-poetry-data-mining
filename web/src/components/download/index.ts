/**
 * @overview
 * file: web/src/components/download/index.ts
 * category: frontend-component
 * tech: TypeScript
 * solved: 提供可复用展示组件与局部交互单元
 * data_source: 组合式状态与组件内部状态
 * data_flow: 状态输入 -> 组件渲染(UI 组件)
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 路径特征: web/src/components/download/index.ts
 */
export { default as PoemsDownloadSection } from './PoemsDownloadSection.vue'
export { default as AuthorsDownloadSection } from './AuthorsDownloadSection.vue'
export { default as WordCountDownloadSection } from './WordCountDownloadSection.vue'
export { default as WordSimDownloadSection } from './WordSimDownloadSection.vue'
export { default as PoemIndexDownloadSection } from './PoemIndexDownloadSection.vue'
export { default as KeywordIndexDownloadSection } from './KeywordIndexDownloadSection.vue'
