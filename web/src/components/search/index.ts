/**
 * @overview
 * file: web/src/components/search/index.ts
 * category: algorithm
 * tech: TypeScript
 * solved: 实现检索与索引策略（核心导出：search api）
 * data_source: 组合式状态与组件内部状态
 * data_flow: 加载索引 -> 匹配过滤 -> 排序分页 -> 返回结果集
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 路径特征: web/src/components/search/index.ts
 */
/**
 * Search Components - 统一搜索UI组件库
 * 
 * 提供三个层次的组件：
 * - SearchInput: 基础搜索输入框
 * - SearchInputEnhanced: 增强版搜索输入（支持建议、历史、高亮）
 * - SearchStats: 搜索统计信息
 * - SearchContainer: 完整搜索容器（整合输入和统计）
 * 
 * 使用示例:
 * ```vue
 * <!-- 基础用法 -->
 * <SearchInput
 *   v-model="searchQuery"
 *   placeholder="搜索诗词..."
 *   @search="handleSearch"
 * />
 * 
 * <!-- 增强版搜索 -->
 * <SearchInputEnhanced
 *   v-model="searchQuery"
 *   placeholder="寻一句诗，觅一位故人..."
 *   :suggestions="poemSuggestions"
 *   :hot-searches="['李白', '杜甫', '静夜思']"
 *   @search="handleSearch"
 * />
 * 
 * <!-- 完整搜索容器 -->
 * <SearchContainer
 *   v-model="searchQuery"
 *   placeholder="搜索诗词..."
 *   :total="totalCount"
 *   :query-time="queryTime"
 *   :source="source"
 *   :loading="isSearching"
 *   @search="handleSearch"
 *   @clear="handleClear"
 * >
 *   <template #filters>
 *     <NSelect v-model:value="dynastyFilter" :options="dynastyOptions" />
 *   </template>
 * </SearchContainer>
 * ```
 */

export { default as SearchInput } from './SearchInput.vue'
export { default as SearchInputEnhanced } from './SearchInputEnhanced.vue'
export { default as SearchStats } from './SearchStats.vue'
export { default as SearchContainer } from './SearchContainer.vue'
