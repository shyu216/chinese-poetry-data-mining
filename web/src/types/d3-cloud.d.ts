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
