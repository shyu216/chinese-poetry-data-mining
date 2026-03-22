import { reactive, readonly, computed } from 'vue'
import type { InjectionKey, Reactive, ComputedRef } from 'vue'

export type LoadingType = 'blocking' | 'background' | 'skeleton'

export interface LoadingTask {
  id: string
  title: string
  description?: string
  progress?: number
  total?: number
  current?: number
  startTime: number
  priority: number
  type: LoadingType  // 加载类型：阻塞/后台/骨架屏
  phase?: string     // 当前阶段
}

export interface LoadingState {
  tasks: Map<string, LoadingTask>
  isLoading: boolean
  currentTask: LoadingTask | null
}

export interface UseLoadingReturn {
  readonly state: Reactive<LoadingState>
  readonly isLoading: ComputedRef<boolean>
  readonly currentTask: ComputedRef<LoadingTask | null>
  readonly progress: ComputedRef<number>
  readonly isBlocking: ComputedRef<boolean>
  readonly isBackground: ComputedRef<boolean>
  start: (options: Omit<LoadingTask, 'id' | 'startTime'>) => string
  update: (id: string, updates: Partial<Omit<LoadingTask, 'id' | 'startTime'>>) => void
  finish: (id: string) => void
  finishAll: () => void
  getTask: (id: string) => LoadingTask | undefined
  // 便捷方法
  startBlocking: (title: string, description?: string, priority?: number) => string
  startBackground: (title: string, description?: string, priority?: number) => string
  startSkeleton: (title: string, description?: string, priority?: number) => string
}

export const LoadingKey: InjectionKey<UseLoadingReturn> = Symbol('loading')

let globalInstance: UseLoadingReturn | null = null

// 诗意的加载阶段文案
const loadingPhases: Record<string, string[]> = {
  init: [
    '正在准备数据索引...',
    '正在建立连接...',
    '正在唤醒服务...',
    '正在整理书架...'
  ],
  meta: [
    '正在读取元数据...',
    '正在解析数据结构...',
    '正在加载配置...',
    '正在校准参数...'
  ],
  search: [
    '正在构建搜索索引...',
    '正在优化查询路径...',
    '正在预热缓存...',
    '正在准备检索引擎...'
  ],
  ui: [
    '正在调整布局...',
    '正在渲染界面...',
    '正在准备画布...',
    '正在排列组件...'
  ],
  data: [
    '正在加载诗词数据...',
    '正在读取诗人档案...',
    '正在整理词频统计...',
    '正在汇聚千年文脉...'
  ],
  render: [
    '正在绘制可视化...',
    '正在生成图表...',
    '正在渲染图形...',
    '正在呈现诗境...'
  ]
}

function generateId(): string {
  return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

function getRandomPhase(phase: string): string {
  const phases = loadingPhases[phase] ?? loadingPhases.init
  if (!phases || phases.length === 0) return '正在加载...'
  const randomPhase = phases[Math.floor(Math.random() * phases.length)]
  return randomPhase ?? '正在加载...'
}

export function useLoading(): UseLoadingReturn {
  if (globalInstance) {
    return globalInstance
  }

  const state = reactive<LoadingState>({
    tasks: new Map(),
    isLoading: false,
    currentTask: null
  })

  const isLoading = computed(() => state.tasks.size > 0)

  const currentTask = computed<LoadingTask | null>(() => {
    if (state.tasks.size === 0) return null
    const tasks = Array.from(state.tasks.values())
    // 阻塞性任务优先显示
    const blockingTasks = tasks.filter(t => t.type === 'blocking')
    if (blockingTasks.length > 0) {
      return blockingTasks.sort((a, b) => b.priority - a.priority)[0] ?? null
    }
    return tasks.sort((a, b) => b.priority - a.priority)[0] ?? null
  })

  const progress = computed(() => {
    const task = currentTask.value
    if (!task) return 0
    if (task.progress !== undefined) return task.progress
    if (task.total && task.total > 0 && task.current !== undefined) {
      return Math.round((task.current / task.total) * 100)
    }
    return 0
  })

  const isBlocking = computed(() => {
    return Array.from(state.tasks.values()).some(t => t.type === 'blocking')
  })

  const isBackground = computed(() => {
    const tasks = Array.from(state.tasks.values())
    return tasks.length > 0 && tasks.every(t => t.type === 'background')
  })

  const start = (options: Omit<LoadingTask, 'id' | 'startTime'>): string => {
    const id = generateId()
    const task: LoadingTask = {
      ...options,
      id,
      startTime: Date.now()
    }
    state.tasks.set(id, task)
    state.isLoading = true
    return id
  }

  const update = (id: string, updates: Partial<Omit<LoadingTask, 'id' | 'startTime'>>): void => {
    const task = state.tasks.get(id)
    if (task) {
      Object.assign(task, updates)
      // 如果更新了 phase，自动更新 description
      if (updates.phase && !updates.description) {
        task.description = getRandomPhase(updates.phase)
      }
    }
  }

  const finish = (id: string): void => {
    state.tasks.delete(id)
    if (state.tasks.size === 0) {
      state.isLoading = false
      state.currentTask = null
    }
  }

  const finishAll = (): void => {
    state.tasks.clear()
    state.isLoading = false
    state.currentTask = null
  }

  const getTask = (id: string): LoadingTask | undefined => {
    return state.tasks.get(id)
  }

  // 便捷方法：阻塞性加载（需要等待）
  const startBlocking = (title: string, description?: string, priority: number = 10): string => {
    return start({
      title,
      description: description || getRandomPhase('init'),
      type: 'blocking',
      priority,
      phase: 'init'
    })
  }

  // 便捷方法：后台加载（可交互）
  const startBackground = (title: string, description?: string, priority: number = 5): string => {
    return start({
      title,
      description: description || getRandomPhase('data'),
      type: 'background',
      priority,
      phase: 'data'
    })
  }

  // 便捷方法：骨架屏加载
  const startSkeleton = (title: string, description?: string, priority: number = 3): string => {
    return start({
      title,
      description: description || getRandomPhase('ui'),
      type: 'skeleton',
      priority,
      phase: 'ui'
    })
  }

  const instance: UseLoadingReturn = {
    state: readonly(state) as Reactive<LoadingState>,
    isLoading,
    currentTask,
    progress,
    isBlocking,
    isBackground,
    start,
    update,
    finish,
    finishAll,
    getTask,
    startBlocking,
    startBackground,
    startSkeleton
  }

  globalInstance = instance
  return instance
}
