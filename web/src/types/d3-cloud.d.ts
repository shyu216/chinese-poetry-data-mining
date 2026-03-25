/**
 * @overview
 * file: web/src/types/d3-cloud.d.ts
 * category: types
 * tech: TypeScript + D3
 * solved: 提供领域模型与第三方库类型声明
 * data_source: TypeScript 声明系统
 * data_flow: 编译期参与类型推导与约束，不参与运行时数据流
 * complexity: 仅编译期类型约束，运行时开销 O(0)
 * unique: 核心导出: scaleLinear, scaleOrdinal, select；关键函数: scaleLinear, scaleOrdinal, select
 */
declare module 'd3-cloud' {
  import { ScaleOrdinal } from 'd3'

  interface Word {
    text: string
    size: number
    x?: number
    y?: number
    rotate?: number
  }

  interface CloudLayout<T> {
    size(size: [number, number]): CloudLayout<T>
    words(words: T[]): CloudLayout<T>
    padding(padding: number): CloudLayout<T>
    rotate(rotate: () => number): CloudLayout<T>
    fontSize(fontSize: (d: T) => number): CloudLayout<T>
    on(event: string, callback: (words: Word[]) => void): CloudLayout<T>
    start(): CloudLayout<T>
  }

  export default function cloud<T>(): CloudLayout<T>
}

declare module 'd3' {
  export function scaleLinear(): any
  export function scaleOrdinal(scheme: string[]): any
  export function select(element: Element | null): any
  export const schemeCategory10: string[]
}
