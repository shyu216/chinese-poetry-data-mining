/**
 * @overview
 * file: web/src/types/d3.d.ts
 * category: types
 * tech: TypeScript + D3
 * solved: 提供领域模型与第三方库类型声明
 * data_source: TypeScript 声明系统
 * data_flow: 编译期参与类型推导与约束，不参与运行时数据流
 * complexity: 仅编译期类型约束，运行时开销 O(0)
 * unique: 核心导出: forceSimulation, forceLink, forceManyBody
 */
declare module 'd3' {
  import { Selection, Event as D3Event, DragBehavior as D3DragBehavior } from 'd3-selection'
  import { ScaleLinear } from 'd3-scale'
  import { ZoomBehavior, ZoomEvent, ZoomTransform } from 'd3-zoom'
  
  // 力导向模拟
  export interface Simulation<NodeDatum, LinkDatum> {
    nodes(nodes: NodeDatum[]): this
    nodes(): NodeDatum[]
    links(links: LinkDatum[]): this
    links(): LinkDatum[]
    force(name: string): any
    force(name: string, force: any): this
    alpha(alpha: number): this
    alphaMin(alpha: number): this
    alphaDecay(alpha: number): this
    alphaTarget(alpha: number): this
    velocityDecay(velocityDecay: number): this
    randomSeed(seed: number): this
    tick(): this
    stop(): this
    restart(): this
    on(typenames: string, callback?: ((event: any) => void) | null): this
    on(): { [key: string]: (event: any) => void }
  }
  
  export function forceSimulation<NodeDatum>(): Simulation<NodeDatum, any>
  export function forceSimulation<NodeDatum>(nodes: NodeDatum[]): Simulation<NodeDatum, any>
  
  // 力函数
  export interface ForceLink<NodeDatum, LinkDatum> {
    id(): (node: NodeDatum) => string
    id(id: (node: NodeDatum) => string): this
    source(): (link: LinkDatum) => NodeDatum | string
    source(source: (link: LinkDatum) => NodeDatum | string): this
    target(): (link: LinkDatum) => NodeDatum | string
    target(target: (link: LinkDatum) => NodeDatum | string): this
    distance(): (link: LinkDatum) => number
    distance(distance: number | ((link: LinkDatum) => number)): this
    strength(): (link: LinkDatum) => number
    strength(strength: number | ((link: LinkDatum) => number)): this
    iterations(number: number): this
  }
  
  export function forceLink<NodeDatum, LinkDatum>(links?: LinkDatum[]): ForceLink<NodeDatum, LinkDatum>
  
  export interface ForceManyBody<NodeDatum> {
    strength(): (node: NodeDatum) => number
    strength(strength: number | ((node: NodeDatum) => number)): this
    theta(theta: number): this
    distanceMin(distanceMin: number): this
    distanceMax(distanceMax: number): this
  }
  
  export function forceManyBody<NodeDatum>(): ForceManyBody<NodeDatum>
  
  export interface ForceCenter<NodeDatum> {
    x(): number
    x(x: number): this
    y(): number
    y(y: number): this
    z(): number
    z(z: number): this
  }
  
  export function forceCenter<NodeDatum>(x: number, y: number, z?: number): ForceCenter<NodeDatum>
  
  export interface ForceCollide<NodeDatum> {
    radius(): (node: NodeDatum) => number
    radius(radius: number | ((node: NodeDatum) => number)): this
    strength(strength: number): this
    iterations(number: number): this
  }
  
  export function forceCollide<NodeDatum>(): ForceCollide<NodeDatum>
  
  // 缩放行为
  export interface ZoomBehavior<Element, Datum> {
    (selection: Selection<Element, Datum, any, any>): void
    scaleExtent([min, max]: [number, number]): this
    translateExtent([min, max]: [number, number]): this
    duration(ms: number): this
    on(typenames: string, callback?: ((event: ZoomEvent<Element, Datum>) => void) | null): this
  }
  
  export function zoom<Element, Datum>(): ZoomBehavior<Element, Datum>
  export const zoomIdentity: ZoomTransform
  
  // 拖拽行为
  export interface DragBehavior<Element, Datum> {
    (selection: Selection<Element, Datum, any, any>): void
    on(typenames: string, callback?: ((event: DragEvent<Element, Datum>, datum: Datum) => void) | null): this
  }
  
  export interface DragEvent<Element, Datum> {
    type: 'start' | 'drag' | 'end'
    target: DragBehavior<Element, Datum>
    subject: {
      x: number
      y: number
      dx: number
      dy: number
    }
    x: number
    y: number
    dx: number
    dy: number
    sourceEvent: PointerEvent
    active: number
  }
  
  export function drag<Element, Datum>(): DragBehavior<Element, Datum>
  
  // 选择器
  export function select<Element extends HTMLElement>(selector: string | Element | null): Selection<Element, any, any, any>
  export function selectAll<Element extends HTMLElement>(selector: string): Selection<Element, any, any, any>
  
  // 类型导出 - 使用原始类型以避免冲突
  export { Selection, D3Event, D3DragBehavior } from 'd3-selection'
  export { ScaleLinear } from 'd3-scale'
  export { ZoomBehavior, ZoomEvent, ZoomTransform } from 'd3-zoom'
  
  // 导出拖拽事件类型
  export { DragEvent }
}