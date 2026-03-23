declare module 'vue-virtual-scroller' {
  import { DefineComponent } from 'vue'
  
  export interface RecycleScrollerProps {
    items: any[]
    itemSize?: number
    minItemSize?: number
    buffer?: number
    pageMode?: boolean
    horizontal?: boolean
    prerender?: number
    estimated?: number
    keyField?: string
    autoResize?: boolean
    resizeObserver?: any
    slotProps?: Record<string, any>
  }
  
  export interface RecycleScrollerInstance {
    updateVisibleItems?: (force?: boolean) => void
    scrollToItem?: (index: number, align?: 'start' | 'center' | 'end') => void
    scrollBy?: (deltaY: number) => void
    scrollTo?: (options: ScrollToOptions) => void
  }
  
  export const RecycleScroller: DefineComponent<RecycleScrollerProps> & {
    new (): RecycleScrollerInstance
  }
  
  export interface ItemSize {
    (item: any, index?: number): number
  }
  
  export interface ResizeObserverEntry {
    contentRect: DOMRectReadOnly
    target: Element
  }
}
