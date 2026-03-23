<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import cloud from 'd3-cloud'
import { NCard, NSpin, NEmpty } from 'naive-ui'
import type { WordCountItem } from '@/composables/types'

interface CloudWordItem {
  text: string
  size: number
  x?: number
  y?: number
  rotate?: number
  count: number
  rank: number
  color: string
}

interface Props {
  words: WordCountItem[]
  maxWords?: number
  width?: number
  height?: number
  minFontSize?: number
  maxFontSize?: number
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  maxWords: 80,
  width: 700,
  height: 350,
  minFontSize: 12,
  maxFontSize: 48,
  loading: false
})

const emit = defineEmits<{
  click: [word: WordCountItem]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const isRendering = ref(false)
const renderedWords = ref<CloudWordItem[]>([])

const colorPalette: string[] = [
  '#8b2635', '#a83246', '#c94a5a', '#e86b7c',
  '#2c3e50', '#34495e', '#5d6d7e', '#7f8c8d',
  '#16a085', '#1abc9c', '#2ecc71', '#27ae60',
  '#2980b9', '#3498db', '#9b59b6', '#8e44ad',
  '#f39c12', '#f1c40f', '#e67e22', '#d35400'
]

const topWords = computed(() => {
  const sorted = [...props.words].sort((a, b) => b.count - a.count)
  return sorted.slice(0, props.maxWords)
})

const maxCount = computed(() => {
  if (topWords.value.length === 0) return 1
  const first = topWords.value[0]
  return first ? first.count : 1
})

const minCount = computed(() => {
  if (topWords.value.length === 0) return 1
  const last = topWords.value[topWords.value.length - 1]
  return last ? last.count : 1
})

const fontSizeScale = (count: number): number => {
  if (maxCount.value === minCount.value) return props.minFontSize
  const ratio = (count - minCount.value) / (maxCount.value - minCount.value)
  return props.minFontSize + ratio * (props.maxFontSize - props.minFontSize)
}

const getWordColor = (index: number): string => {
  return colorPalette[index % colorPalette.length] ?? '#8b2635'
}

interface DragState {
  isDragging: boolean
  hasMoved: boolean
  wordIndex: number
  startX: number
  startY: number
  wordX: number
  wordY: number
}

const DRAG_THRESHOLD = 5 // 移动超过5px认为是拖拽

const dragState: DragState = {
  isDragging: false,
  hasMoved: false,
  wordIndex: -1,
  startX: 0,
  startY: 0,
  wordX: 0,
  wordY: 0
}

// 将 d3-cloud 的中心坐标转换为 Canvas 的左上角坐标
const transformWordPosition = (word: CloudWordItem): { x: number; y: number } => {
  // d3-cloud 的原点在画布中心 (width/2, height/2)
  // Canvas 的原点在左上角 (0, 0)
  const centerX = props.width / 2
  const centerY = props.height / 2
  return {
    x: (word.x ?? 0) + centerX,
    y: (word.y ?? 0) + centerY
  }
}

const renderWordCloud = async () => {
  if (!canvasRef.value || topWords.value.length === 0) return

  isRendering.value = true

  await nextTick()

  // 再次检查 canvasRef，因为在 await 期间组件可能已卸载
  if (!canvasRef.value) {
    isRendering.value = false
    return
  }

  const canvas = canvasRef.value
  const context = canvas.getContext('2d')
  if (!context) {
    isRendering.value = false
    return
  }

  canvas.width = props.width
  canvas.height = props.height

  const layout = cloud<CloudWordItem>()
    .size([props.width, props.height])
    .words(topWords.value.map((w, i) => ({
      text: w.word,
      size: fontSizeScale(w.count),
      count: w.count,
      rank: w.rank,
      color: getWordColor(i)
    })))
    .padding(4)
    .rotate(() => 0)
    .fontSize((d: CloudWordItem) => d.size)
    .on('end', (words: any) => {
      renderedWords.value = words as CloudWordItem[]
      drawWords(words as CloudWordItem[])
      isRendering.value = false
    })

  layout.start()
}

const drawWords = (words: CloudWordItem[]) => {
  const canvas = canvasRef.value
  const context = canvas?.getContext('2d')
  if (!canvas || !context) return

  context.clearRect(0, 0, canvas.width, canvas.height)

  words.forEach((word, index) => {
    context.save()
    context.font = `bold ${word.size}px "Noto Serif SC", "SimSun", serif`
    context.fillStyle = word.color ?? getWordColor(index)
    context.textAlign = 'center'
    context.textBaseline = 'middle'

    const pos = transformWordPosition(word)

    context.fillText(word.text, pos.x, pos.y)
    context.restore()
  })
}

const getWordBounds = (word: CloudWordItem): { left: number; right: number; top: number; bottom: number } => {
  const pos = transformWordPosition(word)
  // 使用 measureText 获取更准确的宽度
  const canvas = canvasRef.value
  const context = canvas?.getContext('2d')
  let textWidth = word.text.length * word.size * 0.8
  if (context) {
    context.font = `bold ${word.size}px "Noto Serif SC", "SimSun", serif`
    const metrics = context.measureText(word.text)
    textWidth = metrics.width
  }
  const wordHeight = word.size * 1.2

  return {
    left: pos.x - textWidth / 2,
    right: pos.x + textWidth / 2,
    top: pos.y - wordHeight / 2,
    bottom: pos.y + wordHeight / 2
  }
}

const handleCanvasClick = (event: MouseEvent) => {
  if (dragState.hasMoved) return // 如果移动过，不触发点击

  if (!canvasRef.value) return

  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const clickedWord = renderedWords.value.find((word: CloudWordItem) => {
    const bounds = getWordBounds(word)
    return (
      x >= bounds.left &&
      x <= bounds.right &&
      y >= bounds.top &&
      y <= bounds.bottom
    )
  })

  if (clickedWord) {
    const wordItem = topWords.value.find(item => item.word === clickedWord.text)
    if (wordItem) {
      emit('click', wordItem)
    }
  }
}

const handleCanvasMouseDown = (event: MouseEvent) => {
  if (!canvasRef.value) return

  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const clickedIndex = renderedWords.value.findIndex((word: CloudWordItem) => {
    const bounds = getWordBounds(word)
    return (
      x >= bounds.left &&
      x <= bounds.right &&
      y >= bounds.top &&
      y <= bounds.bottom
    )
  })

  if (clickedIndex >= 0) {
    const word = renderedWords.value[clickedIndex]
    if (!word) return
    dragState.isDragging = true
    dragState.hasMoved = false
    dragState.wordIndex = clickedIndex
    dragState.startX = x
    dragState.startY = y
    // 存储 d3-cloud 坐标系中的位置
    dragState.wordX = word.x ?? 0
    dragState.wordY = word.y ?? 0
  }
}

const handleCanvasMouseMove = (event: MouseEvent) => {
  if (!dragState.isDragging || !canvasRef.value) return

  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const dx = x - dragState.startX
  const dy = y - dragState.startY

  // 检查是否超过拖拽阈值
  if (!dragState.hasMoved) {
    const distance = Math.sqrt(dx * dx + dy * dy)
    if (distance > DRAG_THRESHOLD) {
      dragState.hasMoved = true
    }
  }

  const word = renderedWords.value[dragState.wordIndex]
  if (word) {
    // 转换回 d3-cloud 坐标系（减去中心点偏移）
    word.x = dragState.wordX + dx
    word.y = dragState.wordY + dy
    drawWords(renderedWords.value)
  }
}

const handleCanvasMouseUp = () => {
  dragState.isDragging = false
  dragState.wordIndex = -1
}

watch(() => props.words, () => {
  if (props.words.length > 0) {
    nextTick(() => {
      renderWordCloud()
    })
  }
}, { deep: true })

onMounted(() => {
  if (topWords.value.length > 0) {
    renderWordCloud()
  }
})

onUnmounted(() => {
  dragState.isDragging = false
  dragState.hasMoved = false
})
</script>

<template>
  <NCard class="wordcloud-card" :content-style="{ padding: '16px' }">
    <template #header>
      <div class="wordcloud-header">
        <span class="title">词云预览</span>
        <span class="subtitle">Top {{ maxWords }} 词汇</span>
      </div>
    </template>

    <NSpin :show="isRendering || loading" size="medium">
      <div
        ref="containerRef"
        class="wordcloud-container"
        :style="{ width: width + 'px', height: height + 'px' }"
      >
        <NEmpty
          v-if="!loading && words.length === 0"
          description="暂无数据"
          :show-icon="false"
        />
        <canvas
          v-else
          ref="canvasRef"
          class="wordcloud-canvas"
          @click="handleCanvasClick"
          @mousedown="handleCanvasMouseDown"
          @mousemove="handleCanvasMouseMove"
          @mouseup="handleCanvasMouseUp"
          @mouseleave="handleCanvasMouseUp"
        />
      </div>
    </NSpin>

    <div class="wordcloud-hint">
      <span>点击词汇查看详情 · 拖拽移动位置</span>
    </div>
  </NCard>
</template>

<style scoped>
.wordcloud-card {
  margin-bottom: 24px;
}

.wordcloud-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.subtitle {
  font-size: 12px;
  color: var(--color-ink-light, #7f8c8d);
}

.wordcloud-container {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated, #fafafa);
  border-radius: 8px;
  overflow: hidden;
  margin: 0 auto;
}

.wordcloud-canvas {
  cursor: pointer;
  transition: cursor 0.2s ease;
}

.wordcloud-canvas:hover {
  cursor: grab;
}

.wordcloud-canvas:active {
  cursor: grabbing;
}

.wordcloud-hint {
  text-align: center;
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-ink-light, #95a5a6);
}
</style>
