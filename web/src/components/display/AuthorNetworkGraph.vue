<!--
  @overview
  file: web/src/components/display/AuthorNetworkGraph.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI + D3
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props；组件事件
  data_flow: props 输入 -> 组件渲染(NCard, NSwitch) -> emit 回传
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: getNodeColor, getNodeRadius, initGraph, resetView；主渲染组件: NCard, NSwitch
-->
<script setup lang="ts">
/**
 * AuthorNetworkGraph - 诗人关系网络图
 * 
 * 使用 D3.js 展示诗人之间的关联关系
 */
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import * as d3 from 'd3'
import { NCard, NSpin, NEmpty, NSlider, NSwitch, NButton } from 'naive-ui'
import { RefreshOutline, ExpandOutline } from '@vicons/ionicons5'

interface AuthorNode {
  id: string
  name: string
  dynasty: string
  poemCount: number
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
  group?: number
}

interface AuthorLink {
  source: string | AuthorNode
  target: string | AuthorNode
  value: number
  type: 'same-era' | 'similar-style' | 'influence'
}

interface Props {
  nodes: AuthorNode[]
  links: AuthorLink[]
  width?: number
  height?: number
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  width: 800,
  height: 600,
  loading: false
})

const emit = defineEmits<{
  'node-click': [node: AuthorNode]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
const simulation = ref<d3.Simulation<AuthorNode, AuthorLink> | null>(null)

// 交互状态
const zoomLevel = ref(1)
const showLabels = ref(true)
const highlightGroup = ref<number | null>(null)
const selectedNode = ref<string | null>(null)

// 朝代颜色映射
const dynastyColors: Record<string, string> = {
  '唐': '#B45309',
  '宋': '#1E40AF',
  '元': '#047857',
  '明': '#7C3AED',
  '清': '#DC2626',
  '近现代': '#0891B2'
}

const getNodeColor = (node: AuthorNode) => {
  return dynastyColors[node.dynasty] || '#5C5244'
}

const getNodeRadius = (node: AuthorNode) => {
  const baseRadius = 8
  const scale = Math.sqrt(node.poemCount / 100)
  return baseRadius + Math.min(scale * 8, 20)
}

// 初始化图表
const initGraph = () => {
  if (!containerRef.value || !svgRef.value || props.nodes.length === 0) return

  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  const width = containerRef.value.clientWidth
  const height = props.height

  // 创建缩放行为
  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.3, 3])
    .on('zoom', (event: d3.ZoomEvent<SVGSVGElement, unknown>) => {
      g.attr('transform', event.transform)
      zoomLevel.value = event.transform.k
    })

  svg.call(zoom)

  // 主容器
  const g = svg.append('g')

  // 创建力导向模拟
  simulation.value = d3.forceSimulation<AuthorNode>(props.nodes)
    .force('link', d3.forceLink<AuthorNode, AuthorLink>(props.links)
      .id(d => typeof d === 'string' ? d : d.id)
      .distance(d => 100 / (d.value * 0.5 + 0.5))
    )
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide<AuthorNode>().radius(d => getNodeRadius(d) + 5))

  // 绘制连线
  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(props.links)
    .enter()
    .append('line')
    .attr('stroke-width', (d: AuthorLink) => Math.sqrt(d.value) * 1.5)
    .attr('stroke', (d: AuthorLink) => {
      switch (d.type) {
        case 'same-era': return 'rgba(139, 38, 53, 0.2)'
        case 'similar-style': return 'rgba(30, 64, 175, 0.2)'
        case 'influence': return 'rgba(180, 83, 9, 0.2)'
        default: return 'rgba(92, 82, 68, 0.15)'
      }
    })
    .attr('stroke-opacity', 0.6)

  // 绘制节点
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(props.nodes)
    .enter()
    .append('g')
    .attr('class', 'node')
    .style('cursor', 'pointer')
    .call(d3.drag<SVGGElement, AuthorNode>()
      .on('start', (event: d3.DragEvent<SVGGElement, AuthorNode>, d: AuthorNode) => {
        if (!event.active && simulation.value) {
          simulation.value.alphaTarget(0.3).restart()
        }
        d.fx = d.x ?? 0
        d.fy = d.y ?? 0
      })
      .on('drag', (event: d3.DragEvent<SVGGElement, AuthorNode>, d: AuthorNode) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event: d3.DragEvent<SVGGElement, AuthorNode>, d: AuthorNode) => {
        if (!event.active && simulation.value) {
          simulation.value.alphaTarget(0)
        }
        d.fx = null
        d.fy = null
      })
    )

  // 节点圆形
  node.append('circle')
    .attr('r', (d: AuthorNode) => getNodeRadius(d))
    .attr('fill', (d: AuthorNode) => getNodeColor(d))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))')
    .style('transition', 'all 0.3s ease')

  // 节点标签
  const labels = node.append('text')
    .text((d: AuthorNode) => d.name)
    .attr('x', (d: AuthorNode) => getNodeRadius(d) + 5)
    .attr('y', 4)
    .attr('font-size', '12px')
    .attr('font-family', '"Noto Serif SC", serif')
    .attr('fill', '#2c3e50')
    .style('opacity', showLabels.value ? 1 : 0)
    .style('pointer-events', 'none')
    .style('text-shadow', '0 1px 2px rgba(255,255,255,0.8)')

  // 交互事件
  node.on('click', (event: MouseEvent, d: AuthorNode) => {
    event.stopPropagation()
    selectedNode.value = selectedNode.value === d.id ? null : d.id
    emit('node-click', d)
  })

  node.on('mouseover', function(this: SVGGElement, event: MouseEvent, d: AuthorNode) {
    d3.select(this).select('circle')
      .transition()
      .duration(200)
      .attr('r', getNodeRadius(d) * 1.2)
      .style('filter', 'drop-shadow(0 4px 8px rgba(0,0,0,0.2))')
    
    // 高亮相关连线
    link.transition()
      .duration(200)
      .attr('stroke-opacity', (l: AuthorLink) => 
        (typeof l.source === 'string' ? l.source : l.source.id) === d.id || 
        (typeof l.target === 'string' ? l.target : l.target.id) === d.id ? 1 : 0.1
      )
  })

  node.on('mouseout', function(this: SVGGElement, event: MouseEvent, d: AuthorNode) {
    d3.select(this).select('circle')
      .transition()
      .duration(200)
      .attr('r', getNodeRadius(d))
      .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))')
    
    link.transition()
      .duration(200)
      .attr('stroke-opacity', 0.6)
  })

  // 更新位置
  simulation.value.on('tick', () => {
    link
      .attr('x1', (d: AuthorLink) => (typeof d.source === 'object' ? d.source.x : 0) ?? 0)
      .attr('y1', (d: AuthorLink) => (typeof d.source === 'object' ? d.source.y : 0) ?? 0)
      .attr('x2', (d: AuthorLink) => (typeof d.target === 'object' ? d.target.x : 0) ?? 0)
      .attr('y2', (d: AuthorLink) => (typeof d.target === 'object' ? d.target.y : 0) ?? 0)

    node.attr('transform', (d: AuthorNode) => `translate(${d.x ?? 0},${d.y ?? 0})`)
  })

  // 监听标签显示
  watch(showLabels, (val) => {
    labels.style('opacity', val ? 1 : 0)
  })
}

// 重置视图
const resetView = () => {
  if (!svgRef.value) return
  const svg = d3.select(svgRef.value)
  svg.transition()
    .duration(750)
    .call(
      d3.zoom<SVGSVGElement, unknown>().transform,
      d3.zoomIdentity
    )
  zoomLevel.value = 1
}

// 监听数据变化
watch(() => props.nodes, () => {
  nextTick(() => initGraph())
}, { deep: true })

watch(() => props.links, () => {
  nextTick(() => initGraph())
}, { deep: true })

onMounted(() => {
  initGraph()
  window.addEventListener('resize', initGraph)
})

onUnmounted(() => {
  if (simulation.value) {
    simulation.value.stop()
  }
  window.removeEventListener('resize', initGraph)
})

// 图例
const legend = [
  { label: '唐代', color: '#B45309' },
  { label: '宋代', color: '#1E40AF' },
  { label: '元代', color: '#047857' },
  { label: '明代', color: '#7C3AED' },
  { label: '清代', color: '#DC2626' }
]
</script>

<template>
  <NCard class="author-network-graph" :bordered="false">
    <template #header>
      <div class="graph-header">
        <h3 class="graph-title">诗人关系网络</h3>
        <div class="graph-controls">
          <NSwitch v-model:value="showLabels" size="small">
            <template #checked>显示标签</template>
            <template #unchecked>隐藏标签</template>
          </NSwitch>
          <NButton size="small" quaternary @click="resetView">
            <template #icon>
              <RefreshOutline />
            </template>
            重置
          </NButton>
        </div>
      </div>
    </template>

    <div class="graph-container" ref="containerRef">
      <NSpin v-if="loading" size="large" class="loading-spin" />
      
      <NEmpty v-else-if="nodes.length === 0" description="暂无数据" />
      
      <svg
        v-else
        ref="svgRef"
        class="graph-svg"
        :width="width"
        :height="height"
      />
    </div>

    <!-- 图例 -->
    <div class="graph-legend">
      <div
        v-for="item in legend"
        :key="item.label"
        class="legend-item"
      >
        <span class="legend-dot" :style="{ background: item.color }" />
        <span class="legend-label">{{ item.label }}</span>
      </div>
    </div>

    <!-- 缩放指示器 -->
    <div class="zoom-indicator">
      <span class="zoom-value">{{ Math.round(zoomLevel * 100) }}%</span>
    </div>
  </NCard>
</template>

<style scoped>
.author-network-graph {
  position: relative;
}

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.graph-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
}

.graph-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.graph-container {
  position: relative;
  width: 100%;
  height: v-bind(height + 'px');
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(139, 38, 53, 0.02) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(201, 169, 110, 0.03) 0%, transparent 50%),
    #fafafa;
  border-radius: 8px;
  overflow: hidden;
}

.loading-spin {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.graph-svg {
  width: 100%;
  height: 100%;
  cursor: grab;
}

.graph-svg:active {
  cursor: grabbing;
}

/* 图例 */
.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  font-size: 12px;
  color: var(--color-ink-light);
}

/* 缩放指示器 */
.zoom-indicator {
  position: absolute;
  bottom: 16px;
  right: 16px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-ink-light);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* D3 样式覆盖 */
:deep(.node circle) {
  transition: all 0.3s ease;
}

:deep(.node:hover circle) {
  stroke: var(--color-seal);
  stroke-width: 3;
}

:deep(.links line) {
  transition: stroke-opacity 0.2s ease;
}

/* 响应式 */
@media (max-width: 768px) {
  .graph-container {
    height: 400px;
  }

  .graph-legend {
    gap: 12px;
  }

  .legend-item {
    font-size: 11px;
  }
}
</style>
