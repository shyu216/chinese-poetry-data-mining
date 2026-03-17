<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NStatistic, NProgress, NTag, NEmpty } from 'naive-ui'
import { 
  AnalyticsOutline, 
  GitCompareOutline,
  SpeedometerOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'

interface Props {
  meterPattern?: string
  poemType?: string
  genre?: string
  meterPatterns?: { pattern: string; count: number }[]
}

const props = defineProps<Props>()

const parsePattern = (pattern: string): number[] => {
  return pattern.split(',').map(n => parseInt(n.trim(), 10)).filter(n => !isNaN(n))
}

const sentenceCounts = computed(() => {
  if (!props.meterPattern) return []
  return parsePattern(props.meterPattern)
})

const lineCount = computed(() => sentenceCounts.value.length)

const avgLineLength = computed(() => {
  if (sentenceCounts.value.length === 0) return 0
  return Math.round(sentenceCounts.value.reduce((a, b) => a + b, 0) / sentenceCounts.value.length)
})

const isRegularVerse = computed(() => {
  if (sentenceCounts.value.length === 0) return false
  const first = sentenceCounts.value[0]
  return sentenceCounts.value.every(n => n === first)
})

const isFourLineVerse = computed(() => lineCount.value === 4)
const isEightLineVerse = computed(() => lineCount.value === 8)

const getMeterCategory = computed(() => {
  const firstCount = avgLineLength.value
  const lines = lineCount.value
  
  if (firstCount === 5 && lines === 4) return { 
    category: '五言绝句', 
    fullName: '五言四句押韵诗',
    desc: '唐代最流行的格律诗体，每句五字，共四句',
    difficulty: 3
  }
  if (firstCount === 5 && lines === 8) return { 
    category: '五言律诗', 
    fullName: '五言八句押韵诗',
    desc: '唐代成熟的格律诗体，每句五字，共八句',
    difficulty: 4
  }
  if (firstCount === 7 && lines === 4) return { 
    category: '七言绝句', 
    fullName: '七言四句押韵诗',
    desc: '唐代最流行的格律诗体，每句七字，共四句',
    difficulty: 3
  }
  if (firstCount === 7 && lines === 8) return { 
    category: '七言律诗', 
    fullName: '七言八句押韵诗',
    desc: '唐代成熟的格律诗体，每句七字，共八句',
    difficulty: 5
  }
  if (firstCount <= 6 && lines > 8) return {
    category: '古体诗',
    fullName: '古体诗',
    desc: '不受严格格律约束的自由诗体',
    difficulty: 1
  }
  return {
    category: '杂言诗',
    fullName: '杂言诗',
    desc: '诗句长短不一的诗歌形式',
    difficulty: 2
  }
})

const patternConsistency = computed(() => {
  if (sentenceCounts.value.length < 2) return 100
  const uniqueLengths = new Set(sentenceCounts.value)
  return Math.round((1 - (uniqueLengths.size - 1) / sentenceCounts.value.length) * 100)
})

const matchingPoemType = computed(() => {
  if (!props.poemType) return null
  const type = props.poemType.replace(/\s/g, '')
  const category = getMeterCategory.value.category.replace(/\s/g, '')
  return type.includes(category.replace(/言/g, '').replace(/句/g, '').replace(/律/g, '').replace(/绝/g, ''))
})

const meterStats = computed(() => {
  const stats: { label: string; value: string | number; icon: any; color: string }[] = []
  
  stats.push({
    label: '句数',
    value: lineCount.value,
    icon: AnalyticsOutline,
    color: '#8b2635'
  })
  
  stats.push({
    label: '平均句长',
    value: `${avgLineLength.value} 字`,
    icon: SpeedometerOutline,
    color: '#1E40AF'
  })
  
  stats.push({
    label: '总字数',
    value: sentenceCounts.value.reduce((a, b) => a + b, 0),
    icon: AnalyticsOutline,
    color: '#047857'
  })
  
  return stats
})

const difficultyStars = computed(() => {
  return Array(5).fill(0).map((_, i) => i < getMeterCategory.value.difficulty)
})
</script>

<template>
  <NCard class="meter-analysis" :bordered="true">
    <template #header>
      <div class="analysis-header">
        <div class="header-icon">
          <GitCompareOutline />
        </div>
        <div class="header-text">
          <h3>格律分析</h3>
          <p>诗句结构与格律特征</p>
        </div>
      </div>
    </template>

    <div v-if="!meterPattern" class="empty-state">
      <NEmpty description="暂无格律数据" />
    </div>

    <div v-else class="analysis-content">
      <div class="meter-type-card">
        <div class="type-badge">
          <span class="type-name">{{ getMeterCategory.category }}</span>
          <span class="type-fullname">{{ getMeterCategory.fullName }}</span>
        </div>
        <p class="type-desc">{{ getMeterCategory.desc }}</p>
        
        <div class="difficulty-bar">
          <span class="difficulty-label">格律难度：</span>
          <div class="difficulty-stars">
            <span 
              v-for="(filled, index) in difficultyStars" 
              :key="index"
              class="star"
              :class="{ filled }"
            >★</span>
          </div>
        </div>
      </div>

      <div class="stats-grid">
        <div 
          v-for="stat in meterStats" 
          :key="stat.label"
          class="stat-item"
        >
          <div class="stat-icon" :style="{ background: `${stat.color}15`, color: stat.color }">
            <component :is="stat.icon" />
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stat.value }}</span>
            <span class="stat-label">{{ stat.label }}</span>
          </div>
        </div>
      </div>

      <div class="consistency-section">
        <div class="consistency-header">
          <span>格律一致性</span>
          <span class="consistency-value">{{ patternConsistency }}%</span>
        </div>
        <NProgress 
          type="line" 
          :percentage="patternConsistency" 
          :show-indicator="false"
          :height="8"
          :border-radius="4"
          :color="isRegularVerse ? '#059669' : '#B45309'"
          :rail-color="isRegularVerse ? 'rgba(5, 150, 105, 0.15)' : 'rgba(180, 83, 9, 0.15)'"
        />
        <div class="consistency-tags">
          <NTag :type="isRegularVerse ? 'success' : 'warning'" size="small">
            <template #icon>
              <component :is="isRegularVerse ? CheckmarkCircleOutline : CloseCircleOutline" />
            </template>
            {{ isRegularVerse ? '齐言诗' : '杂言诗' }}
          </NTag>
          <NTag v-if="isFourLineVerse" type="info" size="small">四句短制</NTag>
          <NTag v-if="isEightLineVerse" type="info" size="small">八句中篇</NTag>
        </div>
      </div>

      <div v-if="meterPatterns && meterPatterns.length > 0" class="similar-patterns">
        <h4>相似格律</h4>
        <div class="pattern-list">
          <div 
            v-for="item in meterPatterns.slice(0, 5)" 
            :key="item.pattern"
            class="pattern-item"
          >
            <span class="pattern-text">{{ item.pattern.replace(/,/g, ' · ') }}</span>
            <span class="pattern-count">{{ item.count }} 首</span>
          </div>
        </div>
      </div>
    </div>
  </NCard>
</template>

<style scoped>
.meter-analysis {
  height: 100%;
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-seal, #8b2635), #a63d4d);
  color: #fff;
  border-radius: 10px;
  font-size: 20px;
}

.header-text h3 {
  margin: 0;
  font-family: "Noto Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.header-text p {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.empty-state {
  padding: 40px 0;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.meter-type-card {
  padding: 16px;
  background: linear-gradient(135deg, rgba(139, 38, 53, 0.05), rgba(139, 38, 53, 0.08));
  border-radius: 10px;
  border: 1px solid rgba(139, 38, 53, 0.1);
}

.type-badge {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.type-name {
  font-family: "Noto Serif SC", serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--color-seal, #8b2635);
}

.type-fullname {
  font-size: 14px;
  color: var(--color-ink-light, #666);
}

.type-desc {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
  line-height: 1.6;
}

.difficulty-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.difficulty-label {
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.difficulty-stars {
  display: flex;
  gap: 2px;
}

.star {
  font-size: 16px;
  color: #e8e8e8;
}

.star.filled {
  color: #B45309;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--color-bg-paper, #fafafa);
  border-radius: 8px;
}

.stat-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 18px;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.stat-label {
  font-size: 12px;
  color: var(--color-ink-light, #999);
}

.consistency-section {
  padding: 16px;
  background: var(--color-bg-paper, #fafafa);
  border-radius: 10px;
}

.consistency-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
}

.consistency-value {
  font-weight: 600;
  color: var(--color-seal, #8b2635);
}

.consistency-tags {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.similar-patterns h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.pattern-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pattern-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-bg-paper, #fafafa);
  border-radius: 6px;
}

.pattern-text {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
}

.pattern-count {
  font-size: 12px;
  color: var(--color-ink-light, #999);
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
