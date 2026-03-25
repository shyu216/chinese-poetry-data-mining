/**
 * @overview
 * file: web/src/search/index.ts
 * category: search
 * tech: TypeScript
 * summary: 项目统一的搜索模块出口，聚合并导出 PoemSearch/AuthorSearch/WordSearch 与相关 composable。
 *
 * Responsibilities:
 *  - 提供组件层友好的入口（usePoemSearch/useAuthorSearch/useWordSearch），隐藏单例初始化细节
 *  - 导出基础工具如 `LRUCache` 以供搜索模块使用
 *
 * Recommendations:
 *  - 在应用启动或路由守卫中预热关键索引以改善首屏搜索体验
 */

// 导出各个搜索模块
export { poemSearch } from './poem/PoemSearch'
export type { PoemSearch, PoemSearchResult, PoemSearchOptions } from './poem/PoemSearch'
export { usePoemSearch } from './poem'

export { authorSearch } from './author/AuthorSearch'
export type { AuthorSearch, AuthorSearchResult, AuthorSearchOptions } from './author/AuthorSearch'
export { useAuthorSearch } from './author'

export { wordSearch } from './word/WordSearch'
export type { WordSearch, WordSearchResult, WordSearchOptions } from './word/WordSearch'
export { useWordSearch } from './word'

// 导出基础组件
export { LRUCache } from './LRUCache'
