/**
 * @overview
 * file: web/src/composables/useShuffle.ts
 * category: utility / composable
 * tech: Vue 3 + TypeScript
 * summary: 提供可复用的洗牌/随机挑选工具（基于 Fisher-Yates），用于在 UI 中随机展示诗词/作者等集合。
 *
 * Data pipeline (conceptual):
 *  - 输入: 一个数组或 `Ref<T[]>` 以及可选的启用开关
 *  - 处理: 生成随机种子 -> 使用 Fisher-Yates 进行伪随机重排 -> 返回 `shuffledItems` 供组件渲染
 *  - 输出: 响应式 `shuffledItems`, 控制函数 `shuffle`, `unshuffle`, `toggleShuffle`
 *
 * Complexity & cost:
 *  - 洗牌算法为 O(n) 时间，O(n) 额外空间（生成副本以保留原数组）
 *  - 频繁洗牌会导致 GC 压力及短期内大量内存分配，应避免在渲染循环中重复触发
 *
 * Exports / responsibilities:
 *  - `useShuffle<T>(options)` -> `shuffledItems`, `isShuffled`, `seed`, `toggleShuffle`, `shuffle`, `unshuffle`
 *  - `getRandomItem`, `getRandomItems` 作为独立工具函数
 *
 * Potential issues & recommendations:
 *  - 若数组非常大（成千上万条），在主线程进行完全洗牌可能阻塞渲染；可选择仅对索引数组做随机抽样或在 Web Worker 中执行洗牌。
 *  - 若需要可复现的顺序（测试或分享），应显式传入/保存 `seed`。
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
