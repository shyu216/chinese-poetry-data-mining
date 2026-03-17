<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { NCard, NEmpty, NSpin, NSlider, NSwitch, NTag, NSpace, NButton, NIcon, NDivider } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'

interface SimilarWord {
  word: string
  similarity: number
}

interface Node {
  id: string
  word: string
  similarity: number
  isCenter: boolean
  x: number
  y: number
  vx: number
  vy: number
  radius: number
}

interface Link {
  source: Node
  target: Node
  strength: number
}

const props = defineProps<{
  centerWord: string
  similarWords: SimilarWord[]
}>()

const emit = defineEmits<{
  (e: 'select-word', word: string): void
}>()

const maxNodes = ref(30)
const showLabels = ref(true)
const minLinkStrength = ref(0.7)
const loading = ref(false)

const graphContainer = ref<HTMLElement | null>(null)
const canvasElement = ref<HTMLCanvasElement | null>(null)

const filteredWords = computed(() => {
  return props.similarWords
    .filter(w => w.similarity >= minLinkStrength.value)
    .slice(0, maxNodes.value)
})

function getNodeColor(similarity: number, isCenter: boolean): string {
  if (isCenter) return '#667eea'
  if (similarity >= 0.9) return '#2ecc71'
  if (similarity >= 0.8) return '#3498db'
  if (similarity >= 0.75) return '#f39c12'
  return '#e74c3c'
}

const simulation = {
  nodes: [] as Node[],
  links: [] as Link[],
  animationId: 0,
  isRunning: false
}

function initGraphData(width: number, height: number) {
  const centerX = width / 2
  const centerY = height / 2
  
  const nodes: Node[] = [
    {
      id: 'center',
      word: props.centerWord,
      similarity: 1,
      isCenter: true,
      x: centerX,
      y: centerY,
      vx: 0,
      vy: 0,
      radius: 35
    }
  ]
  
  const links: Link[] = []
  
  const centerNode = nodes[0]!
  
  filteredWords.value.forEach((sw, index) => {
    const angle = (index / filteredWords.value.length) * Math.PI * 2
    const distance = 100 + (1 - sw.similarity) * 150
    
    const node: Node = {
      id: `node-${index}`,
      word: sw.word,
      similarity: sw.similarity,
      isCenter: false,
      x: centerX + Math.cos(angle) * distance,
      y: centerY + Math.sin(angle) * distance,
      vx: 0,
      vy: 0,
      radius: 20 + sw.similarity * 10
    }
    
    nodes.push(node)
    links.push({
      source: centerNode,
      target: node,
      strength: sw.similarity
    })
  })
  
  return { nodes, links }
}

function simulationStep() {
  const { nodes, links } = simulation
  const centerX = (graphContainer.value?.clientWidth || 800) / 2
  const centerY = (graphContainer.value?.clientHeight || 500) / 2
  
  nodes.forEach(node => {
    if (!node.isCenter) {
      const dx = centerX - node.x
      const dy = centerY - node.y
      node.vx += dx * 0.001
      node.vy += dy * 0.001
    }
  })
  
  links.forEach(link => {
    const dx = link.target.x - link.source.x
    const dy = link.target.y - link.source.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    const targetDist = 120 + (1 - link.strength) * 80
    
    if (dist > 0) {
      const force = (dist - targetDist) * 0.05 * link.strength
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      
      if (!link.source.isCenter) {
        link.source.vx += fx
        link.source.vy += fy
      }
      link.target.vx -= fx
      link.target.vy -= fy
    }
  })
  
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i]!
      const b = nodes[j]!
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      const minDist = a.radius + b.radius + 20
      
      if (dist < minDist && dist > 0) {
        const force = (minDist - dist) * 0.5
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        
        if (!a.isCenter) {
          a.vx -= fx
          a.vy -= fy
        }
        if (!b.isCenter) {
          b.vx += fx
          b.vy += fy
        }
      }
    }
  }
  
  nodes.forEach(node => {
    if (!node.isCenter) {
      node.vx *= 0.9
      node.vy *= 0.9
      node.x += node.vx
      node.y += node.vy
      
      const margin = node.radius + 10
      node.x = Math.max(margin, Math.min((graphContainer.value?.clientWidth || 800) - margin, node.x))
      node.y = Math.max(margin, Math.min((graphContainer.value?.clientHeight || 500) - margin, node.y))
    }
  })
}

function renderCanvas() {
  const canvas = canvasElement.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const width = canvas.width
  const height = canvas.height
  
  ctx.clearRect(0, 0, width, height)
  
  simulation.links.forEach(link => {
    ctx.beginPath()
    ctx.moveTo(link.source.x, link.source.y)
    ctx.lineTo(link.target.x, link.target.y)
    ctx.strokeStyle = `rgba(150, 150, 150, ${link.strength * 0.6})`
    ctx.lineWidth = Math.max(1, link.strength * 4)
    ctx.stroke()
  })
  
  simulation.nodes.forEach(node => {
    ctx.beginPath()
    ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
    ctx.fillStyle = getNodeColor(node.similarity, node.isCenter)
    ctx.fill()
    
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = node.isCenter ? 4 : 2
    ctx.stroke()
    
    ctx.shadowColor = 'rgba(0, 0, 0, 0.2)'
    ctx.shadowBlur = 8
    ctx.shadowOffsetX = 0
    ctx.shadowOffsetY = 2
    
    if (showLabels.value) {
      ctx.shadowColor = 'transparent'
      ctx.fillStyle = '#fff'
      ctx.font = `${node.isCenter ? 'bold 14px' : '12px'} sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.word, node.x, node.y)
      
      if (!node.isCenter) {
        ctx.fillStyle = '#666'
        ctx.font = '10px sans-serif'
        ctx.fillText(`${(node.similarity * 100).toFixed(0)}%`, node.x, node.y + node.radius + 12)
      }
    }
  })
}

function animate() {
  if (!simulation.isRunning) return
  
  simulationStep()
  renderCanvas()
  simulation.animationId = requestAnimationFrame(animate)
}

function startSimulation() {
  simulation.isRunning = true
  animate()
}

function stopSimulation() {
  simulation.isRunning = false
  if (simulation.animationId) {
    cancelAnimationFrame(simulation.animationId)
  }
}

async function renderGraph() {
  if (!graphContainer.value) return
  
  loading.value = true
  stopSimulation()
  await nextTick()
  
  const { width, height } = graphContainer.value.getBoundingClientRect()
  
  let canvas = canvasElement.value
  if (!canvas) {
    canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    graphContainer.value.appendChild(canvas)
    canvasElement.value = canvas
    
    setupCanvasInteraction(canvas)
  } else {
    canvas.width = width
    canvas.height = height
  }
  
  const { nodes, links } = initGraphData(width, height)
  simulation.nodes = nodes
  simulation.links = links
  
  startSimulation()
  
  loading.value = false
}

let hoveredNode: Node | null = null
let isDragging = false
let dragNode: Node | null = null

function setupCanvasInteraction(canvas: HTMLCanvasElement) {
  const getMousePos = (e: MouseEvent) => {
    const rect = canvas.getBoundingClientRect()
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    }
  }
  
  const getNodeAt = (x: number, y: number): Node | null => {
    for (const node of simulation.nodes) {
      const dx = x - node.x
      const dy = y - node.y
      if (dx * dx + dy * dy <= node.radius * node.radius) {
        return node
      }
    }
    return null
  }
  
  canvas.addEventListener('mousemove', (e) => {
    const pos = getMousePos(e)
    
    if (isDragging && dragNode) {
      dragNode.x = pos.x
      dragNode.y = pos.y
      dragNode.vx = 0
      dragNode.vy = 0
      return
    }
    
    const node = getNodeAt(pos.x, pos.y)
    if (node !== hoveredNode) {
      hoveredNode = node
      canvas.style.cursor = node ? 'pointer' : 'default'
    }
  })
  
  canvas.addEventListener('mousedown', (e) => {
    const pos = getMousePos(e)
    const node = getNodeAt(pos.x, pos.y)
    if (node && !node.isCenter) {
      isDragging = true
      dragNode = node
    }
  })
  
  canvas.addEventListener('mouseup', () => {
    isDragging = false
    dragNode = null
  })
  
  canvas.addEventListener('mouseleave', () => {
    isDragging = false
    dragNode = null
  })
  
  canvas.addEventListener('click', (e) => {
    if (isDragging) return
    const pos = getMousePos(e)
    const node = getNodeAt(pos.x, pos.y)
    if (node) {
      emit('select-word', node.word)
    }
  })
  
  let scale = 1
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    scale = Math.max(0.5, Math.min(2, scale * delta))
  })
}

function resetView() {
  renderGraph()
}

watch(() => props.similarWords, () => {
  renderGraph()
}, { deep: true })

watch([maxNodes, minLinkStrength], () => {
  renderGraph()
})

watch(showLabels, () => {
  renderCanvas()
})

onMounted(() => {
  renderGraph()
})

onUnmounted(() => {
  stopSimulation()
})
</script>

<template>
  <NCard class="network-graph-card">
    <div class="graph-controls">
      <NSpace align="center" wrap>
        <div class="control-item">
          <span class="control-label">显示节点数</span>
          <NSlider
            v-model:value="maxNodes"
            :min="5"
            :max="50"
            :step="5"
            style="width: 120px"
          />
          <NTag size="small" type="info">{{ maxNodes }}</NTag>
        </div>
        
        <div class="control-item">
          <span class="control-label">最小相似度</span>
          <NSlider
            v-model:value="minLinkStrength"
            :min="0.7"
            :max="0.9"
            :step="0.05"
            style="width: 120px"
          />
          <NTag size="small" type="info">{{ minLinkStrength.toFixed(2) }}</NTag>
        </div>
        
        <NSwitch v-model:value="showLabels">
          <template #checked>显示标签</template>
          <template #unchecked>隐藏标签</template>
        </NSwitch>
        
        <NButton size="small" @click="resetView">
          <template #icon>
            <NIcon :component="RefreshOutline" />
          </template>
          重置视图
        </NButton>
      </NSpace>
    </div>
    
    <NDivider />
    
    <div class="graph-container-wrapper">
      <NSpin :show="loading" class="graph-spin">
        <div
          ref="graphContainer"
          class="graph-container"
          :style="{ height: '500px' }"
        />
      </NSpin>
      
      <div class="graph-legend">
        <div class="legend-title">相似度图例</div>
        <div class="legend-items">
          <div class="legend-item">
            <div class="legend-color" style="background: #667eea" />
            <span>中心词</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #2ecc71" />
            <span>≥ 0.9 (极高)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #3498db" />
            <span>0.8 - 0.9 (高)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #f39c12" />
            <span>0.75 - 0.8 (中)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: #e74c3c" />
            <span>&lt; 0.75 (一般)</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="graph-hints">
      <NTag size="small" type="info">
        💡 提示：可拖拽节点调整布局，点击节点探索该词
      </NTag>
    </div>
  </NCard>
</template>

<style scoped>
.network-graph-card {
  border-radius: 12px;
}

.graph-controls {
  padding: 8px 0;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}

.graph-container-wrapper {
  position: relative;
}

.graph-container {
  width: 100%;
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
  border-radius: 8px;
  overflow: hidden;
}

.graph-container canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.graph-spin {
  width: 100%;
}

.graph-legend {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
}

.legend-title {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.graph-hints {
  margin-top: 16px;
  text-align: center;
}
</style>
