<!--
  @overview
  file: web/src/components/content/MeterPattern.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(MusicalNotesOutline, NTag, NTooltip)
  complexity: 列表处理常见 O(n)，空间复杂度常见 O(n)
  unique: 主渲染组件: MusicalNotesOutline, NTag, NTooltip
-->
<script setup lang="ts">
import { computed } from 'vue'
import { NTag, NTooltip } from 'naive-ui'
import {MusicalNotesOutline} from '@vicons/ionicons5'

interface Props {
  meterPattern: string
  poemType?: string
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium'
})

const parsePattern = (pattern: string): number[] => {
  return pattern.split(',').map(n => parseInt(n.trim(), 10)).filter(n => !isNaN(n))
}

const sentenceCounts = computed(() => parsePattern(props.meterPattern))

const totalChars = computed(() => 
  sentenceCounts.value.reduce((sum, n) => sum + n, 0)
)

const lineCount = computed(() => sentenceCounts.value.length)

const getMeterType = computed(() => {
  const firstCount = sentenceCounts.value[0] || 0
  const lines = lineCount.value
  
  if (firstCount === 5 && lines === 4) return { type: '五言绝句', abbr: '五绝', color: '#1E40AF' }
  if (firstCount === 5 && lines === 8) return { type: '五言律诗', abbr: '五律', color: '#1E40AF' }
  if (firstCount === 7 && lines === 4) return { type: '七言绝句', abbr: '七绝', color: '#B45309' }
  if (firstCount === 7 && lines === 8) return { type: '七言律诗', abbr: '七律', color: '#B45309' }
  if (firstCount === 6 && lines === 8) return { type: '六言律诗', abbr: '六律', color: '#047857' }
  if (firstCount === 4 && lines === 4) return { type: '四言诗', abbr: '四言', color: '#7C3AED' }
  if (lines > 8) return { type: '古体诗', abbr: '古体', color: '#5C5244' }
  return { type: `${firstCount}言${lines}句`, abbr: `${firstCount}言`, color: '#5C5244' }
})

const patternDisplay = computed(() => {
  return sentenceCounts.value.join(' · ')
})
</script>

<template>
  <div class="meter-pattern" :class="`size-${size}`">
    <div class="meter-icon">
      <MusicalNotesOutline />
    </div>
    <div class="meter-info">
      <NTag 
        :size="size" 
        :bordered="false"
        :style="{ 
          background: `${getMeterType.color}15`, 
          color: getMeterType.color 
        }"
      >
        {{ getMeterType.abbr }}
      </NTag>
      <span class="meter-detail">{{ patternDisplay }}</span>
      <span v-if="poemType" class="poem-type">{{ poemType }}</span>
    </div>
    <NTooltip v-if="lineCount > 0">
      <template #trigger>
        <span class="char-count">{{ totalChars }}字</span>
      </template>
      共 {{ lineCount }} 句，{{ totalChars }} 字
    </NTooltip>
  </div>
</template>

<style scoped>
.meter-pattern {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.meter-pattern:hover {
  border-color: var(--color-seal, #8b2635);
  box-shadow: 0 2px 8px rgba(139, 38, 53, 0.1);
}

.meter-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-seal, #8b2635), #a63d4d);
  color: #fff;
  border-radius: 6px;
  font-size: 16px;
}

.meter-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meter-detail {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
  font-weight: 500;
}

.poem-type {
  font-size: 12px;
  color: var(--color-ink-light, #999);
  padding-left: 8px;
  border-left: 1px solid var(--color-border, #e8e8e8);
}

.char-count {
  font-size: 12px;
  color: var(--color-ink-light, #999);
  cursor: default;
}

.size-small {
  padding: 6px 10px;
  gap: 8px;
}

.size-small .meter-icon {
  width: 26px;
  height: 26px;
  font-size: 14px;
}

.size-small .meter-detail {
  font-size: 13px;
}

.size-large {
  padding: 12px 16px;
  gap: 14px;
}

.size-large .meter-icon {
  width: 40px;
  height: 40px;
  font-size: 20px;
}

.size-large .meter-detail {
  font-size: 16px;
}
</style>
