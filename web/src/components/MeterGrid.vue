<script setup lang="ts">
import { computed } from 'vue'
import { NTooltip, NCollapse, NCollapseItem } from 'naive-ui'
import { GridOutline, ColorPaletteOutline } from '@vicons/ionicons5'

interface Props {
  sentences: string[]
  meterPattern?: string
  showGrid?: boolean
  cellSize?: 'small' | 'medium' | 'large'
  theme?: 'ink' | 'red' | 'blue' | 'green'
}

const props = withDefaults(defineProps<Props>(), {
  showGrid: true,
  cellSize: 'medium',
  theme: 'red'
})

const themeColors = {
  ink: { bg: '#faf8f5', grid: '#d4cfc4', text: '#2c3e50', accent: '#5C5244' },
  red: { bg: '#fef6f6', grid: '#e8d4d4', text: '#2c3e50', accent: '#8b2635' },
  blue: { bg: '#f4f7fc', grid: '#d4dce8', text: '#2c3e50', accent: '#1E40AF' },
  green: { bg: '#f4faf7', grid: '#d4e8dc', text: '#2c3e50', accent: '#047857' }
}

const currentTheme = computed(() => themeColors[props.theme])

const parsePattern = (pattern?: string): number[] => {
  if (!pattern) return []
  return pattern.split(',').map(n => parseInt(n.trim(), 10)).filter(n => !isNaN(n))
}

const sentenceCounts = computed(() => parsePattern(props.meterPattern))

const gridRows = computed(() => {
  const maxChars = Math.max(...sentenceCounts.value, 0)
  return props.sentences.map((sentence, index) => {
    const chars = sentence.split('')
    const expectedCount = sentenceCounts.value[index] || chars.length
    return chars.map((char, charIndex) => ({
      char,
      index: charIndex,
      isExpected: charIndex < expectedCount,
      position: charIndex + 1
    }))
  })
})

const maxCols = computed(() => {
  return Math.max(...gridRows.value.map(row => row.length), 0)
})
</script>

<template>
  <div class="meter-grid-container">
    <div v-if="showGrid" class="grid-header">
      <div class="grid-title">
        <GridOutline />
        <span>米字格</span>
      </div>
      <div class="theme-selector">
        <ColorPaletteOutline />
        <div class="theme-dots">
          <span 
            v-for="(colors, key) in themeColors" 
            :key="key"
            class="theme-dot"
            :class="{ active: key === theme }"
            :style="{ background: colors.accent }"
            @click="$emit('update:theme', key)"
          />
        </div>
      </div>
    </div>

    <div 
      class="meter-grid"
      :class="[`cell-${cellSize}`, { 'show-grid': showGrid }]"
      :style="{
        '--grid-bg': currentTheme.bg,
        '--grid-line': currentTheme.grid,
        '--text-color': currentTheme.text,
        '--accent-color': currentTheme.accent
      }"
    >
      <div 
        v-for="(row, rowIndex) in gridRows" 
        :key="rowIndex"
        class="grid-row"
      >
        <div 
          v-for="(cell, cellIndex) in row" 
          :key="cellIndex"
          class="grid-cell"
          :class="{ 
            'is-expected': cell.isExpected,
            'is-extra': !cell.isExpected,
            'is-last': cellIndex === row.length - 1
          }"
        >
          <NTooltip>
            <template #trigger>
              <span class="cell-char">{{ cell.char }}</span>
            </template>
            第 {{ rowIndex + 1 }} 句 · 第 {{ cell.position }} 字
          </NTooltip>
          <span v-if="showGrid" class="cell-number">{{ cell.position }}</span>
        </div>
        
        <div 
          v-for="n in (maxCols - row.length)" 
          :key="`empty-${n}`"
          class="grid-cell empty"
        >
          <span class="cell-char empty-char">　</span>
        </div>
      </div>
    </div>

    <div v-if="sentenceCounts.length > 0" class="grid-footer">
      <div class="pattern-bar">
        <span class="pattern-label">格律：</span>
        <div class="pattern-blocks">
          <span 
            v-for="(count, index) in sentenceCounts" 
            :key="index"
            class="pattern-block"
            :style="{ 
              width: `${count * 24}px`,
              background: `${currentTheme.accent}20`
            }"
          >
            {{ count }}字
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.meter-grid-container {
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 12px;
  overflow: hidden;
}

.grid-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--color-seal, #8b2635), #a63d4d);
  color: #fff;
}

.grid-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  font-weight: 600;
}

.grid-title svg {
  font-size: 18px;
}

.theme-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  opacity: 0.9;
}

.theme-dots {
  display: flex;
  gap: 6px;
}

.theme-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s;
  border: 2px solid transparent;
}

.theme-dot:hover {
  transform: scale(1.2);
}

.theme-dot.active {
  border-color: #fff;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
}

.meter-grid {
  padding: 20px;
  background: var(--grid-bg);
}

.grid-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.grid-row:last-child {
  margin-bottom: 0;
}

.grid-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.show-grid .grid-cell {
  border: 1px solid var(--grid-line);
}

.grid-cell.is-expected {
  background: #fff;
}

.grid-cell.is-extra {
  background: rgba(220, 38, 38, 0.08);
  border-color: rgba(220, 38, 38, 0.3);
}

.grid-cell.empty {
  background: transparent;
  border: 1px dashed var(--grid-line);
}

.cell-char {
  font-family: "Noto Serif SC", "KaiTi", "楷体", serif;
  font-size: 20px;
  color: var(--text-color);
  line-height: 1;
}

.empty-char {
  color: transparent;
}

.cell-number {
  position: absolute;
  bottom: 2px;
  right: 3px;
  font-size: 8px;
  color: var(--grid-line);
  font-family: sans-serif;
}

.cell-small {
  width: 32px;
  height: 32px;
}

.cell-small .cell-char {
  font-size: 16px;
}

.cell-medium {
  width: 44px;
  height: 44px;
}

.cell-medium .cell-char {
  font-size: 22px;
}

.cell-large {
  width: 56px;
  height: 56px;
}

.cell-large .cell-char {
  font-size: 28px;
}

.grid-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--color-border, #e8e8e8);
}

.pattern-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pattern-label {
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.pattern-blocks {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pattern-block {
  padding: 4px 10px;
  font-size: 12px;
  color: var(--color-ink, #2c3e50);
  border-radius: 4px;
  text-align: center;
}
</style>
