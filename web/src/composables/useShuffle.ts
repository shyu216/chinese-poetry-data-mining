/**
 * @overview
 * file: web/src/composables/useShuffle.ts
 * category: pipeline
 * tech: Vue 3 + TypeScript
 * solved: 封装数据加载与状态编排（关键函数：random, toggleShuffle, shuffle）
 * data_source: 组合式状态与组件内部状态
 * data_flow: 参数输入 -> 读取缓存/远端 -> 数据校验与归一化 -> 输出响应式状态
 * complexity: 列表处理常见 O(n)，空间复杂度常见 O(n)
 * unique: 核心导出: useShuffle, getRandomItem, getRandomItems；关键函数: random, toggleShuffle, shuffle, unshuffle
 */
import { ref, computed, type Ref } from 'vue'

export interface ShuffleOptions<T> {
  items: Ref<T[]> | T[]
  enabled?: Ref<boolean> | boolean
}

export interface ShuffleState {
  isShuffled: Ref<boolean>
  seed: Ref<number>
  toggleShuffle: () => void
  shuffle: () => void
  unshuffle: () => void
}

/**
 * Fisher-Yates 洗牌算法
 */
function fisherYatesShuffle<T>(array: T[], seed: number): T[] {
  const result = [...array]
  let currentSeed = seed

  // 简单的伪随机数生成器
  const random = () => {
    currentSeed = (currentSeed * 9301 + 49297) % 233280
    return currentSeed / 233280
  }

  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    if (i !== j) {
      const temp = result[i]!
      result[i] = result[j]!
      result[j] = temp
    }
  }

  return result
}

/**
 * 生成随机种子
 */
function generateSeed(): number {
  return Math.floor(Math.random() * 1000000)
}

/**
 * 使用 shuffle 功能
 */
export function useShuffle<T>(options: ShuffleOptions<T>): ShuffleState & { shuffledItems: Ref<T[]> } {
  const { items, enabled = true } = options

  const isShuffled = ref(false)
  const seed = ref(generateSeed())

  const itemsRef = computed(() => {
    if (Array.isArray(items)) {
      return items
    }
    return items.value
  })

  const enabledRef = computed(() => {
    if (typeof enabled === 'boolean') {
      return enabled
    }
    return enabled.value
  })

  const shuffledItems = computed(() => {
    if (!enabledRef.value || !isShuffled.value) {
      return itemsRef.value
    }
    return fisherYatesShuffle(itemsRef.value, seed.value)
  })

  const toggleShuffle = () => {
    if (isShuffled.value) {
      unshuffle()
    } else {
      shuffle()
    }
  }

  const shuffle = () => {
    seed.value = generateSeed()
    isShuffled.value = true
  }

  const unshuffle = () => {
    isShuffled.value = false
  }

  return {
    isShuffled,
    seed,
    shuffledItems,
    toggleShuffle,
    shuffle,
    unshuffle
  }
}

/**
 * 随机获取一个元素
 */
export function getRandomItem<T>(items: T[]): T | undefined {
  if (items.length === 0) return undefined
  const index = Math.floor(Math.random() * items.length)
  return items[index]
}

/**
 * 随机获取多个不重复元素
 */
export function getRandomItems<T>(items: T[], count: number): T[] {
  if (items.length === 0) return []
  if (count >= items.length) return [...items]

  const shuffled = fisherYatesShuffle([...items], generateSeed())
  return shuffled.slice(0, count)
}
