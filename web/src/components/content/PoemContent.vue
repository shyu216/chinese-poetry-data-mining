<!--
  @overview
  file: web/src/components/content/PoemContent.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(NSpace, NButton, NIcon)
  complexity: 列表处理常见 O(n)，空间复杂度常见 O(n)
  unique: 关键函数: getCharDelay, toggleMode, toggleExpand, getModeLabel；主渲染组件: NSpace, NButton, NIcon
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { NButton, NIcon, NSpace } from 'naive-ui'
import { TextOutline, GridOutline, ExpandOutline, ContractOutline } from '@vicons/ionicons5'

interface Props {
  sentences: string[]
  mode?: 'text' | 'meter' | 'vertical'
  animate?: boolean
  animationDelay?: number
  showMeters?: boolean
  showControls?: boolean
  title: string
  author: string
  dynasty: string
  genre: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'text',
  animate: true,
  animationDelay: 0,
  showMeters: false,
  showControls: true,
  title: '',
  author: '',
  dynasty: '',
  genre: ''
})

const currentMode = ref(props.mode)
const isExpanded = ref(false)

const displayMode = computed(() => currentMode.value)

// 诗词：每两句一行
const poemPairs = computed(() => {
  const pairs: string[][] = []

  if (props.genre === '诗') {
    // 诗：每两句一行
    for (let i = 0; i < props.sentences.length; i += 2) {
      pairs.push([props.sentences[i] || '', props.sentences[i + 1] || ''])
    }
  } else {
    // 词：每行最多10个字
    let currentLine = ''
    for (const sentence of props.sentences) {
      if (currentLine.length === 0) {
        currentLine = sentence
      } else if (currentLine.length + sentence.length <= 10) {
        currentLine += sentence
      } else {
        pairs.push([currentLine, ''])
        currentLine = sentence
      }
    }
    // 处理最后一行
    if (currentLine) {
      pairs.push([currentLine, ''])
    }
  }

  return pairs
})

// 处理竖排诗句：保持原句格式，不合并
const processedVerticalSentences = computed(() => {
  return props.sentences
})

const getCharDelay = (sentenceIndex: number, charIndex: number) => {
  const baseDelay = props.animationDelay
  const sentenceDelay = sentenceIndex * 200
  const charDelay = charIndex * 30
  return baseDelay + sentenceDelay + charDelay
}

const toggleMode = () => {
  if (currentMode.value === 'text') {
    currentMode.value = 'vertical'
  } else if (currentMode.value === 'vertical') {
    currentMode.value = 'meter'
  } else {
    currentMode.value = 'text'
  }
}

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const getModeLabel = () => {
  switch (currentMode.value) {
    case 'text': return '横排'
    case 'vertical': return '竖排'
    case 'meter': return '格律'
    default: return '横排'
  }
}

const getModeIcon = () => {
  switch (currentMode.value) {
    case 'text': return TextOutline
    case 'vertical': return ExpandOutline
    case 'meter': return GridOutline
    default: return TextOutline
  }
}
</script>

<template>
  <div class="poem-content-wrapper" :class="{ 'is-expanded': isExpanded }">
    <!-- 版式切换控制 -->
    <div v-if="showControls" class="content-controls">
      <NSpace align="center">
        <NButton size="small" quaternary @click="toggleMode">
          <template #icon>
            <NIcon>
              <component :is="getModeIcon()" />
            </NIcon>
          </template>
          {{ getModeLabel() }}
        </NButton>
        <NButton size="small" quaternary @click="toggleExpand">
          <template #icon>
            <NIcon>
              <ContractOutline v-if="isExpanded" />
              <ExpandOutline v-else />
            </NIcon>
          </template>
          {{ isExpanded ? '收起' : '展开' }}
        </NButton>
      </NSpace>
    </div>

    <!-- 诗词内容区域 -->
    <div class="poem-content" :class="`mode-${displayMode}`">
      <!-- 竖排古典版式 - 上下排列，从右到左 -->
      <template v-if="displayMode === 'vertical'">
        <div class="vertical-layout-new">


          <!-- 竖排正文 - 上下排列，从右到左 -->
          <div class="vertical-body-new">
            <div v-for="(sentence, index) in processedVerticalSentences" :key="index" class="vertical-sentence-new"
              :class="{ 'animate-in': animate }"
              :style="animate ? { animationDelay: `${animationDelay + index * 150}ms` } : {}">
              <span v-for="(char, charIndex) in sentence.split('')" :key="charIndex" class="vertical-char-new">
                {{ char }}
              </span>
            </div>
          </div>

        </div>
      </template>

      <!-- 横排版式 -->
      <template v-else-if="displayMode === 'text'">
        <div class="text-layout">
          <!-- 诗词：每两句一行，用空格分隔 -->
          <p v-for="(pair, pairIndex) in poemPairs" :key="pairIndex" class="poem-line"
            :class="{ 'animate-in': animate }"
            :style="animate ? { animationDelay: `${animationDelay + pairIndex * 100}ms` } : {}">
            <span class="sentence-part">{{ pair[0] || '' }}</span>
            <span class="sentence-separator">　</span>
            <span class="sentence-part">{{ pair[1] || '' }}</span>
          </p>
        </div>
      </template>

      <!-- 格律版式 -->
      <template v-else-if="displayMode === 'meter'">
        <div class="meter-layout">
          <div class="meter-grid">
            <div v-for="(sentence, rowIndex) in sentences" :key="rowIndex" class="meter-row">
              <div v-for="(char, charIndex) in sentence.split('')" :key="charIndex" class="meter-cell"
                :class="{ 'animate-in': animate }"
                :style="animate ? { animationDelay: `${getCharDelay(rowIndex, charIndex)}ms` } : {}"
                :title="`第${rowIndex + 1}句 · 第${charIndex + 1}字`">
                {{ char }}
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* 外层容器 */
.poem-content-wrapper {
  position: relative;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.poem-content-wrapper.is-expanded {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.98);
  padding: 40px;
  overflow: auto;
}

/* 控制栏 */
.content-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(139, 38, 53, 0.1);
}

/* 诗词内容基础 */
.poem-content {
  font-family: "Noto Serif SC", "Source Han Serif SC", "STSong", "SimSun", serif;
}

/* ========== 竖排古典版式 - 新布局 ========== */
.vertical-layout-new {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  background:
    linear-gradient(to right, rgba(139, 38, 53, 0.02) 0%, transparent 10%, transparent 90%, rgba(139, 38, 53, 0.02) 100%),
    linear-gradient(to bottom, rgba(139, 38, 53, 0.01) 0%, transparent 20%);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

/* 竖排标题 */
.vertical-header-new {
  text-align: center;
  margin-bottom: 30px;
}

.vertical-title-new {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink, #2c3e50);
  margin: 0 0 12px 0;
  letter-spacing: 4px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.05);
}

.vertical-meta-new {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.dynasty-seal-new {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-seal, #8b2635);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(139, 38, 53, 0.3);
}

.author-name-new {
  font-size: 16px;
  color: var(--color-ink-light, #666);
}

/* 竖排正文 - 上下排列，从右到左 */
.vertical-body-new {
  display: flex;
  flex-direction: row-reverse;
  /* 从右到左 */
  flex-wrap: wrap;
  justify-content: center;
  gap: 24px 32px;
  padding: 20px 0;
  max-width: 100%;
}

.vertical-sentence-new {
  display: flex;
  flex-direction: column;
  /* 上下排列 */
  align-items: center;
  gap: 2px;
  margin: 0;
  opacity: 1;
}

.vertical-sentence-new.animate-in {
  opacity: 0;
  animation: verticalFadeInNew 0.8s ease forwards;
}

.vertical-char-new {
  font-size: 22px;
  color: var(--color-ink, #2c3e50);
  line-height: 1.8;
  letter-spacing: 2px;
  transition: all 0.3s ease;
}

.vertical-char-new:hover {
  color: var(--color-seal, #8b2635);
  transform: scale(1.1);
}

@keyframes verticalFadeInNew {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 装饰 */
.vertical-decoration-new {
  position: absolute;
  bottom: 20px;
  right: 20px;
}

.seal-mark-new {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 30% 30%, rgba(139, 38, 53, 0.9) 0%, rgba(139, 38, 53, 0.7) 100%);
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  border-radius: 4px;
  box-shadow:
    inset 0 0 10px rgba(0, 0, 0, 0.2),
    0 2px 8px rgba(139, 38, 53, 0.3);
  opacity: 0.9;
}

/* ========== 横排版式 ========== */
.text-layout {
  padding: 20px;
}

.mode-text .poem-line {
  font-size: 18px;
  line-height: 2;
  color: var(--color-ink, #2c3e50);
  margin: 0 0 16px;
  text-align: center;
  letter-spacing: 2px;
  opacity: 1;
}

.mode-text .poem-line.animate-in {
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
}

.mode-text .poem-line:last-child {
  margin-bottom: 0;
}

.mode-text .sentence-part {
  display: inline;
}

.mode-text .sentence-separator {
  display: inline;
  padding: 0 1em;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========== 格律版式 ========== */
.meter-layout {
  padding: 20px;
}

.meter-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.meter-row {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.meter-cell {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--color-ink, #2c3e50);
  background:
    linear-gradient(to right, rgba(139, 38, 53, 0.1) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(139, 38, 53, 0.1) 1px, transparent 1px),
    linear-gradient(45deg, transparent 49.5%, rgba(139, 38, 53, 0.05) 49.5%, rgba(139, 38, 53, 0.05) 50.5%, transparent 50.5%),
    linear-gradient(-45deg, transparent 49.5%, rgba(139, 38, 53, 0.05) 49.5%, rgba(139, 38, 53, 0.05) 50.5%, transparent 50.5%);
  background-size:
    50% 100%,
    100% 50%,
    100% 100%,
    100% 100%;
  background-position: center;
  border: 1px solid rgba(139, 38, 53, 0.15);
  border-radius: 4px;
  transition: all 0.2s ease;
  opacity: 1;
}

.meter-cell.animate-in {
  opacity: 0;
  transform: scale(0.8);
  animation: cellPopIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.meter-cell:hover {
  background-color: rgba(139, 38, 53, 0.05);
  border-color: rgba(139, 38, 53, 0.3);
  transform: scale(1.05);
}

@keyframes cellPopIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .vertical-layout {
    gap: 20px;
    padding: 20px 10px;
  }

  .vertical-title {
    font-size: 22px;
    letter-spacing: 4px;
  }

  .vertical-char {
    font-size: 18px;
  }

  .vertical-body {
    gap: 20px;
  }

  .mode-text .poem-sentence {
    font-size: 16px;
    line-height: 1.8;
  }

  .meter-cell {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .content-controls {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .vertical-char {
    font-size: 16px;
  }

  .meter-cell {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }

  .seal-mark {
    width: 36px;
    height: 36px;
    font-size: 16px;
  }
}
</style>