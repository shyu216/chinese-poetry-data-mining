/**
 * @overview
 * file: web/src/search/index.ts
 * category: algorithm
 * tech: TypeScript
 * solved: 实现检索与索引策略（核心导出：search api）
 * data_source: 组合式状态与组件内部状态
 * data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 路径特征: web/src/search/index.ts
 */
/**
 * Search Modules - 统一搜索模块入口
 *
 * 提供三个独立的搜索模块：
 * - PoemSearch: 诗词搜索（关键词、标题、作者、朝代、体裁）
 * - AuthorSearch: 作者搜索（作者名、朝代）
 * - WordSearch: 词汇搜索（词汇、词长度、频次）
 *
 * 使用示例:
 * ```ts
 * import { usePoemSearch, useAuthorSearch, useWordSearch } from '@/search'
 *
 * // 诗词搜索
 * const { search: searchPoems, isReady: poemSearchReady } = usePoemSearch()
 * const result = await searchPoems('李白', { limit: 10, filters: { dynasty: '唐' } })
 *
 * // 作者搜索
 * const { search: searchAuthors, isReady: authorSearchReady } = useAuthorSearch()
 * const authors = await searchAuthors('杜甫')
 *
 * // 词汇搜索
 * const { search: searchWords, isReady: wordSearchReady } = useWordSearch()
 * const words = await searchWords('明月', { filters: { minLength: 2 } })
 * ```
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
