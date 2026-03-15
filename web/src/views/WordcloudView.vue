<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import * as d3 from 'd3'
import cloud from 'd3-cloud'
import { NCard, NSpin, NSelect, NDataTable, NTag } from 'naive-ui'
import { usePoems } from '@/composables/usePoems'

const { getAllPoems } = usePoems()

interface WordFreq {
  word: string
  frequency: number
}

const loading = ref(true)
const wordcloudRef = ref<HTMLDivElement | null>(null)
const wordFreq = ref<WordFreq[]>([])
const selectedDynasty = ref<string | null>(null)

const dynastyOptions = [
  { label: '全部', value: 'all' },
  { label: '唐', value: '唐' },
  { label: '宋', value: '宋' },
  { label: '元', value: '元' },
  { label: '明', value: '明' },
  { label: '清', value: '清' }
]

const columns = [
  { title: '排名', key: 'rank', width: 80 },
  { title: '词语', key: 'word' },
  { title: '出现次数', key: 'frequency', sorter: true }
]

onMounted(async () => {
  try {
    await renderWordcloud('all')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const filterByDynasty = async (dynasty: string | null) => {
  selectedDynasty.value = dynasty
  await renderWordcloud(dynasty || 'all')
}

const renderWordcloud = async (dynasty: string) => {
  if (!wordcloudRef.value) return

  const poemsData = await getAllPoems(dynasty !== 'all' ? { dynasty } : undefined, 1, 10000)
  let poems = poemsData.poems

  const wordCounts: Record<string, number> = {}
  poems.forEach((p: PoemSummary) => {
    const words = (p.title || '').split('').filter((w: string) => w.length > 1)
    words.forEach((word: string) => {
      wordCounts[word] = (wordCounts[word] || 0) + 1
    })
  })

  const sortedWords = Object.entries(wordCounts)
    .map(([word, frequency]) => ({ word, frequency }))
    .sort((a, b) => b.frequency - a.frequency)
    .slice(0, 100)

  wordFreq.value = sortedWords.map((w, i) => ({ ...w, rank: i + 1 }))

  wordcloudRef.value.innerHTML = ''

  const width = wordcloudRef.value.clientWidth
  const height = 400

  const maxFreq = Math.max(...sortedWords.map(w => w.frequency))
  const minFreq = Math.min(...sortedWords.map(w => w.frequency))

  const fontSize = d3.scaleLinear()
    .domain([minFreq, maxFreq])
    .range([14, 48])

  const color = d3.scaleOrdinal(d3.schemeCategory10)

  const layout = cloud<WordFreq>()
    .size([width, height])
    .words(sortedWords)
    .padding(5)
    .rotate(() => (Math.random() > 0.5 ? 0 : 90) * (Math.random() > 0.5 ? 1 : -1))
    .fontSize((d: WordFreq) => fontSize(d.frequency))
    .on('end', draw)

  layout.start()

  interface CloudWord extends WordFreq {
    x: number
    y: number
    rotate: number
    size: number
  }

  function draw(words: CloudWord[]) {
    const svg = d3.select(wordcloudRef.value)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2})`)

    svg.selectAll('text')
      .data(words)
      .enter()
      .append('text')
      .style('font-size', (d: any) => `${d.size}px`)
      .style('font-family', 'Impact, sans-serif')
      .style('fill', (d: any, i: number) => color(i.toString()))
      .attr('text-anchor', 'middle')
      .attr('transform', (d: any) => `translate(${d.x}, ${d.y}) rotate(${d.rotate})`)
      .text((d: any) => d.text)
  }
}
</script>

<template>
  <div class="wordcloud-view">
    <NCard title="词云展示">
      <div class="filter-bar">
        <NSelect
          v-model:value="selectedDynasty"
          :options="dynastyOptions"
          placeholder="选择朝代"
          style="width: 150px"
          @update:value="filterByDynasty"
        />
      </div>

      <NSpin :show="loading">
        <div ref="wordcloudRef" class="wordcloud-container"></div>

        <div class="freq-table">
          <h3>词频统计 Top 50</h3>
          <NDataTable
            :columns="columns"
            :data="wordFreq.slice(0, 50)"
            :bordered="false"
            :single-line="false"
            size="small"
          />
        </div>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.wordcloud-view {
  max-width: 1200px;
  margin: 0 auto;
}

.filter-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.wordcloud-container {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 24px;
  overflow: hidden;
}

.freq-table h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #333;
}

@media (max-width: 768px) {
  .wordcloud-page {
    padding: 16px;
  }

  .page-header h1 {
    font-size: 24px;
  }

  .page-header p {
    font-size: 14px;
  }

  .controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .control-group {
    width: 100%;
  }

  .control-group span {
    min-width: auto;
  }

  .wordcloud-container {
    height: 400px;
  }

  .freq-table {
    max-height: 300px;
  }
}
</style>
