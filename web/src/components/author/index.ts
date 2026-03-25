/**
 * 文件: web/src/components/author/index.ts
 * 说明: author 组件目录的导出入口，统一对外暴露 `AuthorCard`、`AuthorList` 与 `AuthorClusterViz` 及相关类型。
 *
 * 角色与数据流:
 *   - 仅负责导出/类型组织，不包含业务逻辑或数据请求。
 *   - 上层页面/容器通过导出组件接入呈现与交互逻辑。
 *
 * 复杂度:
 *   - 常数时间导出模块引用 O(1)，实际渲染复杂度由所引用组件决定（如 `AuthorList` 为 O(n)）。
 *
 * 建议/注意事项:
 *   - 保持导出清单与组件文件同步，避免循环依赖。
 */
export { default as AuthorCard } from './AuthorCard.vue'
export { default as AuthorList } from './AuthorList.vue'
export { default as AuthorClusterViz } from './AuthorClusterViz.vue'
export type { AuthorListItem } from './AuthorList.vue'
