<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Props {
  isSearching: boolean
  currentChunk: number
  totalChunks: number
  foundCount: number
  keyword: string
}

const props = defineProps<Props>()

const isVisible = computed(() => props.isSearching && props.currentChunk > 0)

const progressPercent = computed(() => {
  if (props.totalChunks === 0) return 0
  return Math.round((props.currentChunk / props.totalChunks) * 100)
})

// 诗意化的搜索提示
const searchHints: string[] = [
  '正在诗海中寻觅...',
  '正在翻阅古籍...',
  '正在搜集佳句...',
  '正在探访诗人...',
  '正在整理文脉...'
]

const currentHint = ref<string>(searchHints[0]!)

// 每5秒更换一次提示
let hintInterval: ReturnType<typeof setInterval> | null = null

watch(() => props.isSearching, (searching) => {
  if (searching) {
    currentHint.value = searchHints[0]!
    hintInterval = setInterval(() => {
      const currentIndex = searchHints.indexOf(currentHint.value)
      if (currentIndex !== -1) {
        const nextHint = searchHints[(currentIndex + 1) % searchHints.length]
        if (nextHint) {
          currentHint.value = nextHint
        }
      }
    }, 5000)
  } else {
    if (hintInterval) {
      clearInterval(hintInterval)
      hintInterval = null
    }
  }
})
</script>

<template>
  <Transition name="float-slide">
    <div v-if="isVisible" class="search-progress-float">
      <div class="float-content">
        <div class="float-header">
          <span class="float-icon">🔍</span>
          <span class="float-title">{{ currentHint }}</span>
        </div>
        <div class="float-body">
          <div class="progress-info">
            <span class="chunk-info">正在查找第 {{ currentChunk }} / {{ totalChunks }} 分块</span>
            <span v-if="foundCount > 0" class="found-badge">
              已找到 {{ foundCount }} 首
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.search-progress-float {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(139, 38, 53, 0.1);
  padding: 16px 20px;
  min-width: 280px;
  max-width: 320px;
}

.float-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.float-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.float-icon {
  font-size: 18px;
  animation: pulse 2s ease-in-out infinite;
}

.float-title {
  font-size: 14px;
  font-weight: 500;
  color: #8B2635;
  font-family: 'Noto Serif SC', serif;
}

.float-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.chunk-info {
  color: #666;
}

.found-badge {
  background: linear-gradient(135deg, #8B2635, #a03040);
  color: white;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  animation: fadeIn 0.3s ease;
}

.progress-bar {
  height: 4px;
  background: rgba(139, 38, 53, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #8B2635, #C9A96E);
  border-radius: 2px;
  transition: width 0.3s ease;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 进入/退出动画 */
.float-slide-enter-active,
.float-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.float-slide-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.float-slide-leave-to {
  opacity: 0;
  transform: translateX(100px);
}

/* 响应式 */
@media (max-width: 768px) {
  .search-progress-float {
    top: auto;
    bottom: 20px;
    right: 16px;
    left: 16px;
    min-width: auto;
    max-width: none;
  }
}
</style>
