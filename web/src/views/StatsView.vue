<script setup lang="ts">
import { ref, onMounted, shallowRef } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { NCard, NSpin, NSelect, NTag } from 'naive-ui'
import { usePoems } from '@/composables/usePoems'
import { useAuthors } from '@/composables/useAuthors'

const { loadSummary } = usePoems()
const { loadAuthors } = useAuthors()

const loading = ref(true)
const dynastyChartRef = ref<HTMLDivElement | null>(null)
const genreChartRef = ref<HTMLDivElement | null>(null)
const topAuthorsChartRef = ref<HTMLDivElement | null>(null)
const selectedDynasty = ref<string | null>(null)
const dynastyOptions = ref<Array<{ label: string; value: string }>>([])

const dynasties = [
  { label: '唐', value: '唐' },
  { label: '宋', value: '宋' },
  { label: '元', value: '元' },
  { label: '明', value: '明' },
  { label: '清', value: '清' }
]

const dynastyColors: Record<string, string> = {
  '唐': '#c41e3a',
  '宋': '#2080f0',
  '元': '#18a058',
  '明': '#f0a020',
  '清': '#9c27b0'
}

onMounted(async () => {
  try {
    const poemsData = await loadSummary()
    const authorsData = await loadAuthors()

    dynastyOptions.value = [
      { label: '全部', value: 'all' },
      ...Object.keys(dynastyColors).map(d => ({ label: d, value: d }))
    ]

    renderDynastyChart(poemsData.poems)
    renderGenreChart(poemsData.poems)
    renderTopAuthorsChart(authorsData.authors)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const renderDynastyChart = (poems: any[]) => {
  if (!dynastyChartRef.value) return

  const counts: Record<string, number> = {}
  poems.forEach(p => {
    counts[p.dynasty] = (counts[p.dynasty] || 0) + 1
  })

  const data = [{
    values: Object.values(counts),
    labels: Object.keys(counts),
    type: 'pie',
    marker: {
      colors: Object.keys(counts).map(d => dynastyColors[d] || '#999')
    },
    textinfo: 'label+percent',
    hole: 0.4
  }]

  const layout = {
    title: '诗词朝代分布',
    height: 350,
    margin: { t: 40, b: 20, l: 20, r: 20 }
  }

  Plotly.newPlot(dynastyChartRef.value, data, layout, { displayModeBar: false })
}

const renderGenreChart = (poems: any[]) => {
  if (!genreChartRef.value) return

  const counts: Record<string, number> = {}
  poems.forEach(p => {
    counts[p.genre] = (counts[p.genre] || 0) + 1
  })

  const data = [{
    x: Object.keys(counts),
    y: Object.values(counts),
    type: 'bar',
    marker: {
      color: '#c41e3a'
    }
  }]

  const layout = {
    title: '诗词体裁分布',
    height: 350,
    margin: { t: 40, b: 40, l: 60, r: 20 },
    xaxis: { title: '体裁' },
    yaxis: { title: '数量' }
  }

  Plotly.newPlot(genreChartRef.value, data, layout, { displayModeBar: false })
}

const renderTopAuthorsChart = (authors: Record<string, any>) => {
  if (!topAuthorsChartRef.value) return

  const sorted = Object.entries(authors)
    .map(([name, data]) => ({ name, count: data.poem_count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 15)

  const data = [{
    x: sorted.map(a => a.count),
    y: sorted.map(a => a.name),
    type: 'bar',
    orientation: 'h',
    marker: {
      color: '#c41e3a'
    }
  }]

  const layout = {
    title: '高产作者 Top 15',
    height: 400,
    margin: { t: 40, b: 40, l: 100, r: 20 },
    xaxis: { title: '诗歌数量' },
    yaxis: { title: '作者' }
  }

  Plotly.newPlot(topAuthorsChartRef.value, data, layout, { displayModeBar: false })
}

const filterByDynasty = async (dynasty: string | null) => {
  selectedDynasty.value = dynasty
  const poemsData = await loadSummary()
  
  let poems = poemsData.poems
  if (dynasty && dynasty !== 'all') {
    poems = poems.filter(p => p.dynasty === dynasty)
  }
  
  renderGenreChart(poems)
}
</script>

<template>
  <div class="stats-view">
    <NCard title="统计仪表板">
      <NSpin :show="loading">
        <div class="charts-grid">
          <div class="chart-container">
            <div ref="dynastyChartRef"></div>
          </div>
          
          <div class="chart-container">
            <div class="filter-bar">
              <NSelect
                v-model:value="selectedDynasty"
                :options="dynastyOptions"
                placeholder="选择朝代"
                style="width: 150px"
                @update:value="filterByDynasty"
              />
            </div>
            <div ref="genreChartRef"></div>
          </div>
          
          <div class="chart-container full-width">
            <div ref="topAuthorsChartRef"></div>
          </div>
        </div>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.stats-view {
  max-width: 1200px;
  margin: 0 auto;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.chart-container {
  min-height: 380px;
}

.chart-container.full-width {
  grid-column: 1 / -1;
}

.filter-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
