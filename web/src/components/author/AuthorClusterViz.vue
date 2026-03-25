<!--
  文件: web/src/components/author/AuthorClusterViz.vue
  说明: 聚类可视化组件，提供 2D 散点画布与列表/统计视图，展示基于聚类算法得到的作者分组（流派）。

  数据管线:
    - 输入: 父组件通过 props 提供 `clusters`（聚类元信息）与 `authors`（含二维坐标 coord_2d、聚类 id 等）。
    - 处理: 在客户端将坐标缩放/偏移到画布坐标系，绘制聚类中心与散点；交互事件（mousemove/click）在画布上计算最近点并触发回调。
    - 输出: 通过 `emit('selectAuthor')` / 路由跳转导出用户选择或聚类详情动作。

  复杂度:
    - 绘制与交互的核心循环为 O(n)，n = authors.length；若在 `mousemove` 频繁触发，将导致每帧 O(n) 计算与重绘。
    - 空间复杂度 O(n + k)，k = clusters.length，内存用于存放坐标与聚类元信息。

  使用技术/要点:
    - 直接使用原生 Canvas API 绘制点、中心与文本，避免大量 DOM 节点开销。
    - 采用预计算的 scale/offset 转换坐标，减少每次计算的重复工作。

  潜在问题与改进建议:
    - 性能: `handleMouseMove` 对每个鼠标事件遍历所有点 (O(n))，建议使用空间索引（四叉树或 kd-tree）或节流/节省重绘策略以支持大规模点集（数万级）。
    - 分辨率: 未处理 devicePixelRatio，画布在高 DPI 屏幕上可能模糊，应按 DPR 缩放画布尺寸并放大绘制内容。
    - 响应式: 画布宽高为固定常量，缺乏容器自适应，移动端/小屏设备需要自适配方案。
    - 可维护性: 颜色与 alpha 组合直接字符串拼接，需确保 `cluster.color` 为标准 6 位 HEX，否则可能导致无效颜色。
    - 事件解绑/内存: 目前在组件生命周期中未显式添加全局监听，但若后续添加需保证解绑以防泄露。
    - 无辅助图层/缩放控制，建议加入缩放、平移和点密度聚合（聚合层）提高大规模数据可视化体验。
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NTabs, NTabPane, NSpin, NEmpty, NTag, NSpace, NButton, NIcon } from 'naive-ui'
import { PeopleOutline, BookOutline } from '@vicons/ionicons5'
import type { AuthorCluster, AuthorNode } from '@/types/cluster'

interface Props {
  clusters: AuthorCluster[]
  authors: AuthorNode[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  selectAuthor: [author: AuthorNode]
  selectCluster: [clusterId: number]
}>()

const router = useRouter()

const goToClusterDetail = (clusterId: number) => {
  router.push(`/authors/clusters/${clusterId}`)
}

const formatNumber = (num: number): string => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

const activeTab = ref('2d')
const selectedCluster = ref<number | null>(null)
const hoveredAuthor = ref<AuthorNode | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

// 画布配置
const CANVAS_WIDTH = 800
const CANVAS_HEIGHT = 500
const POINT_RADIUS = 4
const HOVER_RADIUS = 8

// 计算缩放比例
const scaleX = computed(() => {
  if (!props.authors.length) return 1
  const coords = props.authors.map(a => a.coord_2d[0])
  const min = Math.min(...coords)
  const max = Math.max(...coords)
  return CANVAS_WIDTH / (max - min + 20) || 1
})

const scaleY = computed(() => {
  if (!props.authors.length) return 1
  const coords = props.authors.map(a => a.coord_2d[1])
  const min = Math.min(...coords)
  const max = Math.max(...coords)
  return CANVAS_HEIGHT / (max - min + 20) || 1
})

const offsetX = computed(() => {
  if (!props.authors.length) return 0
  const coords = props.authors.map(a => a.coord_2d[0])
  return -Math.min(...coords) + 10
})

const offsetY = computed(() => {
  if (!props.authors.length) return 0
  const coords = props.authors.map(a => a.coord_2d[1])
  return -Math.min(...coords) + 10
})

// 转换坐标
const transformCoord = (coord: [number, number]): [number, number] => {
  return [
    (coord[0] + offsetX.value) * scaleX.value,
    (coord[1] + offsetY.value) * scaleY.value
  ]
}

// 绘制2D散点图
const draw2D = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // 清空画布
  ctx.fillStyle = '#fafafa'
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
  
  // 绘制网格
  ctx.strokeStyle = '#e0e0e0'
  ctx.lineWidth = 1
  for (let i = 0; i < CANVAS_WIDTH; i += 50) {
    ctx.beginPath()
    ctx.moveTo(i, 0)
    ctx.lineTo(i, CANVAS_HEIGHT)
    ctx.stroke()
  }
  for (let i = 0; i < CANVAS_HEIGHT; i += 50) {
    ctx.beginPath()
    ctx.moveTo(0, i)
    ctx.lineTo(CANVAS_WIDTH, i)
    ctx.stroke()
  }
  
  // 绘制聚类中心
  props.clusters.forEach(cluster => {
    const [x, y] = transformCoord(cluster.center_2d as [number, number])
    ctx.beginPath()
    ctx.arc(x, y, 15, 0, Math.PI * 2)
    ctx.fillStyle = cluster.color + '30'
    ctx.fill()
    ctx.strokeStyle = cluster.color
    ctx.lineWidth = 2
    ctx.stroke()
    
    // 绘制标签
    ctx.fillStyle = cluster.color
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(cluster.name, x, y - 20)
    ctx.font = '10px sans-serif'
    ctx.fillStyle = '#666'
    ctx.fillText(`${cluster.size}人`, x, y - 8)
  })
  
  // 绘制诗人点
  props.authors.forEach(author => {
    const [x, y] = transformCoord(author.coord_2d)
    const cluster = props.clusters.find(c => c.id === author.cluster)
    const color = cluster?.color || '#999'
    
    // 如果选中某个聚类，淡化其他聚类
    const isDimmed = selectedCluster.value !== null && author.cluster !== selectedCluster.value
    const alpha = isDimmed ? 0.2 : 0.8
    
    ctx.beginPath()
    ctx.arc(x, y, POINT_RADIUS, 0, Math.PI * 2)
    ctx.fillStyle = color + Math.floor(alpha * 255).toString(16).padStart(2, '0')
    ctx.fill()
    
    // 高亮悬停
    if (hoveredAuthor.value?.id === author.id) {
      ctx.beginPath()
      ctx.arc(x, y, HOVER_RADIUS, 0, Math.PI * 2)
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.stroke()
    }
  })
}

// 处理鼠标移动
const handleMouseMove = (e: MouseEvent) => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  // 找到最近的诗人
  let nearest: AuthorNode | null = null
  let minDist = Infinity
  
  props.authors.forEach(author => {
    const [x, y] = transformCoord(author.coord_2d)
    const dist = Math.sqrt((mouseX - x) ** 2 + (mouseY - y) ** 2)
    if (dist < HOVER_RADIUS && dist < minDist) {
      minDist = dist
      nearest = author
    }
  })
  
  hoveredAuthor.value = nearest
  draw2D()
}

// 处理点击
const handleClick = () => {
  if (hoveredAuthor.value) {
    emit('selectAuthor', hoveredAuthor.value)
  }
}

// 监听数据变化
watch(() => [props.authors, props.clusters, selectedCluster.value], () => {
  if (activeTab.value === '2d') {
    draw2D()
  }
}, { deep: true })

onMounted(() => {
  draw2D()
})
</script>

<template>
  <NCard class="cluster-viz-card" :content-style="{ padding: '16px' }">
    <template #header>
      <div class="cluster-header">
        <span class="title">诗人流派聚类</span>
        <span class="subtitle">基于词频和诗体特征的谱聚类分析</span>
      </div>
    </template>

    <NSpin :show="loading" size="large">
      <NEmpty v-if="!loading && (!authors.length || !clusters.length)" description="暂无数据" />
      
      <div v-else class="cluster-content">
        <NTabs v-model:value="activeTab" type="line" animated>
          <NTabPane name="2d" tab="2D分布">
            <!-- 聚类筛选 -->
            <div class="cluster-filters">
              <NSpace>
                <NButton 
                  size="small" 
                  :type="selectedCluster === null ? 'primary' : 'default'"
                  @click="selectedCluster = null"
                >
                  全部流派
                </NButton>
                <NButton
                  v-for="cluster in clusters"
                  :key="cluster.id"
                  size="small"
                  :type="selectedCluster === cluster.id ? 'primary' : 'default'"
                  :style="{ borderColor: cluster.color, color: selectedCluster === cluster.id ? '#fff' : cluster.color }"
                  @click="selectedCluster = selectedCluster === cluster.id ? null : cluster.id"
                >
                  {{ cluster.name }} ({{ cluster.size }})
                </NButton>
              </NSpace>
            </div>
            
            <div class="viz-container">
              <canvas
                ref="canvasRef"
                :width="CANVAS_WIDTH"
                :height="CANVAS_HEIGHT"
                class="cluster-canvas"
                @mousemove="handleMouseMove"
                @click="handleClick"
              />
              
              <!-- 悬停提示 -->
              <div v-if="hoveredAuthor" class="hover-tooltip">
                <div class="author-name">{{ hoveredAuthor.name }}</div>
                <div class="author-info">
                  <NTag size="tiny" :color="{ 
                    color: clusters.find(c => c.id === hoveredAuthor?.cluster)?.color + '20',
                    textColor: clusters.find(c => c.id === hoveredAuthor?.cluster)?.color 
                  }">
                    {{ clusters.find(c => c.id === hoveredAuthor?.cluster)?.name }}
                  </NTag>
                  <span>{{ hoveredAuthor.poem_count }}首</span>
                </div>
              </div>
            </div>
          </NTabPane>

          <NTabPane name="list" tab="流派列表">
            <div class="clusters-list">
              <div
                v-for="cluster in clusters"
                :key="cluster.id"
                class="cluster-item-wrapper"
                :class="{ active: selectedCluster === cluster.id }"
                @click="goToClusterDetail(cluster.id)"
              >
                <NCard class="cluster-item" hoverable>
                  <div class="cluster-item-content">
                    <!-- 左侧：颜色标识和名称 -->
                    <div class="cluster-item-left">
                      <div class="cluster-color-bar" :style="{ background: cluster.color }"></div>
                      <div class="cluster-main-info">
                        <h3 class="cluster-item-name">{{ cluster.name }}</h3>
                        <div class="cluster-item-meta">
                          <span class="meta-item">
                            <NIcon :size="14"><PeopleOutline /></NIcon>
                            {{ formatNumber(cluster.size) }}人
                          </span>
                          <span class="meta-item">
                            <NIcon :size="14"><BookOutline /></NIcon>
                            平均{{ cluster.avg_poems }}首诗
                          </span>
                        </div>
                      </div>
                    </div>

                    <!-- 中间：代表诗人 -->
                    <div class="cluster-item-section">
                      <div class="section-label">代表诗人</div>
                      <div class="authors-list-horizontal">
                        <span 
                          v-for="(author, i) in cluster.representatives.slice(0, 5)" 
                          :key="i"
                          class="author-item"
                        >
                          {{ author }}
                        </span>
                        <span v-if="cluster.representatives.length > 5" class="more-authors">
                          +{{ cluster.representatives.length - 5 }}
                        </span>
                      </div>
                    </div>

                    <!-- 右侧：特色词汇 -->
                    <div class="cluster-item-section">
                      <div class="section-label">特色词汇</div>
                      <div class="words-list-horizontal">
                        <NTag
                          v-for="(word, i) in cluster.top_words.slice(0, 4)"
                          :key="i"
                          size="small"
                          :bordered="false"
                          type="info"
                        >
                          {{ word.word }}
                        </NTag>
                      </div>
                    </div>
                  </div>
                </NCard>
              </div>
            </div>
          </NTabPane>

          <NTabPane name="stats" tab="统计">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ authors.length }}</div>
                <div class="stat-label">诗人</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ clusters.length }}</div>
                <div class="stat-label">流派</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ Math.round(authors.reduce((a, b) => a + b.poem_count, 0) / authors.length) }}</div>
                <div class="stat-label">平均诗数</div>
              </div>
            </div>
            
            <div class="cluster-distribution">
              <h4>流派分布</h4>
              <div class="distribution-bars">
                <div
                  v-for="cluster in clusters"
                  :key="cluster.id"
                  class="dist-bar"
                  :style="{ 
                    width: (cluster.size / authors.length * 100) + '%',
                    backgroundColor: cluster.color 
                  }"
                  :title="`${cluster.name}: ${cluster.size}人`"
                />
              </div>
            </div>
          </NTabPane>
        </NTabs>
      </div>
    </NSpin>
  </NCard>
</template>

<style scoped>
.cluster-viz-card {
  margin-bottom: 24px;
}

.cluster-header {
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

.cluster-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cluster-filters {
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.viz-container {
  position: relative;
  display: flex;
  justify-content: center;
  padding: 16px;
}

.cluster-canvas {
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  background: #fafafa;
  cursor: crosshair;
}

.hover-tooltip {
  position: absolute;
  top: 16px;
  right: 16px;
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 150px;
}

.author-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.clusters-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.cluster-item-wrapper {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.cluster-item-wrapper:hover {
  transform: translateX(4px);
}

.cluster-item-wrapper.active .cluster-item {
  box-shadow: 0 4px 16px rgba(139, 38, 53, 0.15);
  border-color: var(--color-seal, #8b2635);
}

.cluster-item {
  width: 100%;
}

.cluster-item-content {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 0;
}

.cluster-item-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
  flex-shrink: 0;
}

.cluster-color-bar {
  width: 6px;
  height: 48px;
  border-radius: 3px;
  flex-shrink: 0;
}

.cluster-main-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cluster-item-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
}

.cluster-item-meta {
  display: flex;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-ink-light);
}

.cluster-item-section {
  flex: 1;
  min-width: 150px;
}

.section-label {
  font-size: 11px;
  color: var(--color-ink-light);
  margin-bottom: 6px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.authors-list-horizontal {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.author-item {
  font-size: 13px;
  color: var(--color-ink);
  padding: 3px 8px;
  background: var(--color-bg-paper);
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

.more-authors {
  font-size: 11px;
  color: var(--color-ink-light);
  padding: 3px 8px;
}

.words-list-horizontal {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: var(--color-bg-elevated, #fafafa);
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-seal, #8b2635);
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.cluster-distribution {
  padding: 16px;
  background: var(--color-bg-elevated, #fafafa);
  border-radius: 8px;
}

.cluster-distribution h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
}

.distribution-bars {
  display: flex;
  height: 32px;
  border-radius: 4px;
  overflow: hidden;
}

.dist-bar {
  height: 100%;
  transition: opacity 0.2s;
  cursor: pointer;
}

.dist-bar:hover {
  opacity: 0.8;
}
</style>
