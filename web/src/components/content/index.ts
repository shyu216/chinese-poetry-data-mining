/**
 * @overview
 * file: web/src/components/content/index.ts
 * category: frontend-component
 * tech: TypeScript
 * solved: 提供可复用展示组件与局部交互单元
 * data_source: 组合式状态与组件内部状态
 * data_flow: 状态输入 -> 组件渲染(UI 组件)
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 路径特征: web/src/components/content/index.ts
 */
export { default as PoemContent } from './PoemContent.vue'
export { default as PoemCard } from './PoemCard.vue'
export { default as MeterPattern } from './MeterPattern.vue'
export { default as SchoolCard } from './SchoolCard.vue'
