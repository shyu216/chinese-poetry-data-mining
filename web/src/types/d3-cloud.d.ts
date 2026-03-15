declare module 'd3-cloud' {
  import { h } from 'd3'
  
  interface CloudWord {
    x?: number
    y?: number
    rotate?: number
    size?: number
    text?: string
  }

  interface CloudLayout<T> {
    size(): [number, number]
    size(size: [number, number]): this
    words(): T[]
    words(words: T[]): this
    padding(): number
    padding(padding: number): this
    spiral(): string | ((size: [number, number]) => [number, number])
    spiral(spiral: string | ((size: [number, number]) => [number, number])): this
    font(): string | ((d: T) => string)
    font(font: string | ((d: T) => string)): this
    fontSize(): ((d: T) => number) | number
    fontSize(size: ((d: T) => number) | number): this
    fontStyle(): string | ((d: T) => string)
    fontStyle(style: string | ((d: T) => string)): this
    fontWeight(): string | ((d: T) => string | number)
    fontWeight(weight: string | ((d: T) => string | number)): this
    rotate(): ((d: T) => number) | number
    rotate(rotate: ((d: T) => number) | number): this
    text(): ((d: T) => string) | string
    text(text: ((d: T) => string) | string): this
    on(): this
    on(type: string): ((d: T[], bounds: { x0: number, y0: number, x1: number, y1: number }) => void) | undefined
    on(type: string, listener: (d: T[], bounds: { x0: number, y0: number, x1: number, y1: number }) => void): this
    start(): this
    stop(): this
  }

  function layoutcloud<T>(): CloudLayout<T>

  export default layoutcloud
  export { CloudWord, CloudLayout }
}
