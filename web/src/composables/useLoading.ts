import { reactive, readonly, computed } from 'vue'
import type { InjectionKey, Reactive, ComputedRef } from 'vue'

// Loading 模式
export type LoadingMode = 'blocking' | 'non-blocking' | 'idle'

// Loading 阶段 - 诗意化
export type LoadingPhase =
  | 'init'      // 初始化
  | 'connect'   // 连接中
  | 'metadata'  // 读取元数据
  | 'data'      // 加载数据
  | 'search'    // 搜索中
  | 'render'    // 渲染中
  | 'complete'  // 完成
  | 'error'     // 错误

// 统一 Loading 状态
export interface UnifiedLoadingState {
  mode: LoadingMode           // 当前模式
  phase: LoadingPhase         // 当前阶段
  title: string              // 主标题
  description: string        // 描述文案
  progress: number           // 进度 0-100
  current: number            // 当前进度数值
  total: number              // 总数值
  startTime: number          // 开始时间
  canCancel: boolean         // 是否可取消
  error?: string             // 错误信息
}

// 诗意文案库
const phaseDescriptions: Record<LoadingPhase, string[]> = {
  init: [
    '文脉初启，正在唤醒千年诗魂...',
    '墨香浮动，正在铺展宣纸...',
    '笔尖轻触，正在研墨调锋...',
    '诗心初动，正在开启文脉...'
  ],
  connect: [
    '正在架设通往诗海的桥梁...',
    '正在拨动连接古今的琴弦...',
    '正在打开通往文脉的大门...',
    '正在架设跨越时空的诗廊...'
  ],
  metadata: [
    '正在翻阅诗词典藏目录...',
    '正在整理诗人名录档案...',
    '正在检索千年文脉索引...',
    '正在梳理浩瀚诗海脉络...'
  ],
  data: [
    '正在汇聚唐诗宋词精华...',
    '正在采撷历代诗词瑰宝...',
    '正在装载千古诗文典籍...',
    '正在汇聚千年诗词精华...'
  ],
  search: [
    '正在诗海中寻觅佳句...',
    '正在古籍中搜寻踪迹...',
    '正在词林间探寻意境...',
    '正在诗山词海中寻访...'
  ],
  render: [
    '正在描绘诗意画卷...',
    '正在勾勒文字之美...',
    '正在呈现诗境风华...',
    '正在渲染诗词意境...'
  ],
  complete: [
    '文脉已通，请君品鉴...',
    '诗海已开，任君遨游...',
    '墨香已至，静候赏析...',
    '诗词已备，请君雅赏...'
  ],
  error: [
    '墨尽纸枯，请稍后再试...',
    '文脉暂断，正在重连...',
    '诗海起波，请刷新页面...',
    '加载遇阻，请稍后重试...'
  ]
}

// 获取随机文案
function getRandomDescription(phase: LoadingPhase): string {
  const descriptions = phaseDescriptions[phase]
  const randomIndex = Math.floor(Math.random() * descriptions.length)
  return descriptions[randomIndex] ?? '正在加载...'
}

// 计算进度百分比
function calculateProgress(current: number, total: number): number {
  if (total === 0) return 0
  return Math.min(Math.round((current / total) * 100), 100)
}

export interface UseUnifiedLoadingReturn {
  // 状态（只读）
  readonly state: Reactive<UnifiedLoadingState>
  readonly isLoading: ComputedRef<boolean>
  readonly isBlocking: ComputedRef<boolean>
  readonly isNonBlocking: ComputedRef<boolean>
  readonly progressPercent: ComputedRef<number>
  readonly elapsedTime: ComputedRef<number>

  // 核心方法
  startBlocking: (title: string, description?: string) => void
  startNonBlocking: (title: string, description?: string) => void
  update: (updates: Partial<Omit<UnifiedLoadingState, 'mode' | 'startTime'>>) => void
  updatePhase: (phase: LoadingPhase, description?: string) => void
  updateProgress: (current: number, total: number, description?: string) => void
  finish: () => void
  error: (message: string) => void

  // 便捷方法 - 预定义流程
  startViewLoad: (viewName: string) => void
  startSearch: (keyword: string) => void
  startDataFetch: (dataType: string) => void
}

export const LoadingKey: InjectionKey<UseUnifiedLoadingReturn> = Symbol('loading')

let globalInstance: UseUnifiedLoadingReturn | null = null

export function useLoading(): UseUnifiedLoadingReturn {
  if (globalInstance) {
    return globalInstance
  }

  // 初始状态
  const state = reactive<UnifiedLoadingState>({
    mode: 'idle',
    phase: 'init',
    title: '',
    description: '',
    progress: 0,
    current: 0,
    total: 0,
    startTime: 0,
    canCancel: false
  })

  // 计算属性
  const isLoading = computed(() => state.mode !== 'idle')
  const isBlocking = computed(() => state.mode === 'blocking')
  const isNonBlocking = computed(() => state.mode === 'non-blocking')
  const progressPercent = computed(() => state.progress)
  const elapsedTime = computed(() => {
    if (state.startTime === 0) return 0
    return Date.now() - state.startTime
  })

  // 开始 blocking loading
  const startBlocking = (title: string, description?: string): void => {
    state.mode = 'blocking'
    state.phase = 'init'
    state.title = title
    state.description = description || getRandomDescription('init')
    state.progress = 0
    state.current = 0
    state.total = 0
    state.startTime = Date.now()
    state.canCancel = false
    state.error = undefined
  }

  // 开始 non-blocking loading
  const startNonBlocking = (title: string, description?: string): void => {
    state.mode = 'non-blocking'
    state.phase = 'search'
    state.title = title
    state.description = description || getRandomDescription('search')
    state.progress = 0
    state.current = 0
    state.total = 0
    state.startTime = Date.now()
    state.canCancel = true
    state.error = undefined
  }

  // 通用更新方法
  const update = (updates: Partial<Omit<UnifiedLoadingState, 'mode' | 'startTime'>>): void => {
    if (state.mode === 'idle') return

    if (updates.phase) {
      state.phase = updates.phase
    }
    if (updates.title) {
      state.title = updates.title
    }
    if (updates.description) {
      state.description = updates.description
    }
    if (updates.current !== undefined) {
      state.current = updates.current
    }
    if (updates.total !== undefined) {
      state.total = updates.total
    }
    if (updates.progress !== undefined) {
      state.progress = updates.progress
    } else if (updates.current !== undefined && updates.total !== undefined) {
      state.progress = calculateProgress(updates.current, updates.total)
    }
    if (updates.canCancel !== undefined) {
      state.canCancel = updates.canCancel
    }
    if (updates.error !== undefined) {
      state.error = updates.error
    }
  }

  // 更新阶段
  const updatePhase = (phase: LoadingPhase, description?: string): void => {
    if (state.mode === 'idle') return

    state.phase = phase
    state.description = description || getRandomDescription(phase)

    // 自动设置进度（如果没有明确设置）
    if (phase === 'complete') {
      state.progress = 100
    } else if (phase === 'error') {
      state.error = state.error || getRandomDescription('error')
    }
  }

  // 更新进度
  const updateProgress = (current: number, total: number, description?: string): void => {
    if (state.mode === 'idle') return

    state.current = current
    state.total = total
    state.progress = calculateProgress(current, total)

    if (description) {
      state.description = description
    }
  }

  // 完成 loading
  const finish = (): void => {
    // 先显示完成状态
    if (state.mode !== 'idle') {
      state.phase = 'complete'
      state.description = getRandomDescription('complete')
      state.progress = 100

      // 延迟重置状态，让用户看到完成状态
      setTimeout(() => {
        state.mode = 'idle'
        state.phase = 'init'
        state.title = ''
        state.description = ''
        state.progress = 0
        state.current = 0
        state.total = 0
        state.startTime = 0
        state.canCancel = false
        state.error = undefined
      }, 300)
    }
  }

  // 错误处理
  const error = (message: string): void => {
    state.phase = 'error'
    state.error = message
    state.description = message

    // 3秒后自动清除错误状态
    setTimeout(() => {
      if (state.phase === 'error') {
        finish()
      }
    }, 3000)
  }

  // 便捷方法：开始页面加载
  const startViewLoad = (viewName: string): void => {
    const titles: Record<string, string> = {
      'home': '文脉初启',
      'poems': '诗词典藏',
      'authors': '诗人名录',
      'author-detail': '诗人详情',
      'poem-detail': '诗词详情',
      'keyword': '词境探幽',
      'wordcount': '词频统计',
      'data': '数据管理'
    }
    startBlocking(titles[viewName] || viewName, getRandomDescription('init'))
  }

  // 便捷方法：开始搜索
  const startSearch = (keyword: string): void => {
    startNonBlocking('诗海寻踪', `正在搜寻"${keyword}"...`)
  }

  // 便捷方法：开始数据获取
  const startDataFetch = (dataType: string): void => {
    const titles: Record<string, string> = {
      'poems': '正在汇聚诗词...',
      'authors': '正在整理诗人...',
      'words': '正在统计词频...',
      'metadata': '正在读取索引...'
    }
    startNonBlocking('数据加载', titles[dataType] || '正在加载数据...')
  }

  const instance: UseUnifiedLoadingReturn = {
    state: readonly(state) as Reactive<UnifiedLoadingState>,
    isLoading,
    isBlocking,
    isNonBlocking,
    progressPercent,
    elapsedTime,
    startBlocking,
    startNonBlocking,
    update,
    updatePhase,
    updateProgress,
    finish,
    error,
    startViewLoad,
    startSearch,
    startDataFetch
  }

  globalInstance = instance
  return instance
}

// 重置全局实例（用于测试）
export function resetLoading(): void {
  globalInstance = null
}
