/**
 * Search Components - 统一搜索UI组件库
 * 
 * 提供三个层次的组件：
 * - SearchInput: 基础搜索输入框
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
export { default as SearchStats } from './SearchStats.vue'
export { default as SearchContainer } from './SearchContainer.vue'
