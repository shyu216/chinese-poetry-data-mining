/**
 * @overview
 * file: web/src/types/plotly.d.ts
 * category: types
 * tech: TypeScript
 * solved: 提供领域模型与第三方库类型声明
 * data_source: TypeScript 声明系统
 * data_flow: 编译期参与类型推导与约束，不参与运行时数据流
 * complexity: 仅编译期类型约束，运行时开销 O(0)
 * unique: 路径特征: web/src/types/plotly.d.ts
 */
declare module 'plotly.js-dist-min' {
  const Plotly: any
  export default Plotly
}
