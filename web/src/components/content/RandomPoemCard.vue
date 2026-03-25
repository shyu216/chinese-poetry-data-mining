<!--
  @overview
  file: web/src/components/content/RandomPoemCard.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Vue Router + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 组合式状态与组件内部状态
  data_flow: 状态输入 -> 组件渲染(RefreshOutline, NSpin, DynastyBadge) -> 路由联动
  complexity: 列表处理常见 O(n)，空间复杂度常见 O(n)
  unique: 关键函数: startCountdown, stopCountdown, fetchRandomPoem, refreshRandomPoem；主渲染组件: RefreshOutline, NSpin, DynastyBadge
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { NSpin } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { DynastyBadge } from '@/components/ui/badge'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { getRandomItem } from '@/composables/useShuffle'
import type { PoemDetail } from '@/composables/types'

const router = useRouter()
const { loadChunkDetails, totalChunks } = usePoemsV2()

const randomPoem = ref<PoemDetail | null>(null)
const displayedSentences = ref<string[]>([])
const isLoading = ref(false)
const loadedPoems = ref<PoemDetail[]>([])

// 倒计时相关
const COUNTDOWN_SECONDS = 30
const countdown = ref(COUNTDOWN_SECONDS)
const countdownProgress = ref(100)
let countdownInterval: number | null = null
let progressInterval: number | null = null

// 开始倒计时
const startCountdown = () => {
  // 清除之前的定时器
  if (countdownInterval) clearInterval(countdownInterval)
  if (progressInterval) clearInterval(progressInterval)

  countdown.value = COUNTDOWN_SECONDS
  countdownProgress.value = 100

  // 每秒更新倒计时
  countdownInterval = window.setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      refreshRandomPoem()
    }
  }, 1000)

  // 平滑更新进度条
  const updateInterval = 100
  const step = 100 / (COUNTDOWN_SECONDS * 1000 / updateInterval)
  progressInterval = window.setInterval(() => {
    countdownProgress.value -= step
    if (countdownProgress.value <= 0) {
      countdownProgress.value = 100
    }
  }, updateInterval)
}

// 停止倒计时
const stopCountdown = () => {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
}

// 从诗词中随机抽取1-2句金句
const extractRandomSentences = (sentences: string[]): string[] => {
  if (!sentences || sentences.length === 0) return []
  
  // 如果只有1-2句，全部展示
  if (sentences.length <= 2) return sentences
  
  // 随机选择连续1-2句
  const maxStartIndex = sentences.length - 1
  const startIndex = Math.floor(Math.random() * maxStartIndex)
  const count = Math.random() > 0.5 ? 2 : 1
  
  return sentences.slice(startIndex, startIndex + count)
}

// 获取随机诗词
const fetchRandomPoem = async () => {
  isLoading.value = true

  try {
    // 如果还没有加载任何诗词，先加载一些
    if (loadedPoems.value.length === 0) {
      const totalChunkCount = totalChunks.value || 10
      const randomChunkIds = Array.from({ length: 3 }, () =>
        Math.floor(Math.random() * totalChunkCount)
      )

      for (const chunkId of randomChunkIds) {
        try {
          const poemMap = await loadChunkDetails(chunkId)
          if (poemMap && poemMap.size > 0) {
            const poems = Array.from(poemMap.values())
            loadedPoems.value.push(...poems)
          }
        } catch (e) {
          console.warn(`Failed to load chunk ${chunkId}`)
        }
      }
    }

    // 从已加载的诗词中随机选择
    if (loadedPoems.value.length > 0) {
      const selectedPoem = getRandomItem(loadedPoems.value)
      randomPoem.value = selectedPoem || null
      if (selectedPoem?.sentences) {
        displayedSentences.value = extractRandomSentences(selectedPoem.sentences)
      }
    }
  } finally {
    isLoading.value = false
  }
}

// 刷新随机诗词
const refreshRandomPoem = () => {
  if (loadedPoems.value.length > 0) {
    let newPoem = getRandomItem(loadedPoems.value)
    // 避免连续两次随机到同一首
    while (newPoem && newPoem.id === randomPoem.value?.id && loadedPoems.value.length > 1) {
      newPoem = getRandomItem(loadedPoems.value)
    }
    randomPoem.value = newPoem || null
    if (newPoem?.sentences) {
      displayedSentences.value = extractRandomSentences(newPoem.sentences)
    }
    // 刷新后重新开始倒计时
    startCountdown()
  } else {
    fetchRandomPoem()
  }
}

// 跳转到详情页
const goToDetail = () => {
  if (randomPoem.value) {
    if (randomPoem.value.chunk_id !== undefined) {
      router.push({
        path: `/poems/${randomPoem.value.id}`,
        query: { chunk_id: randomPoem.value.chunk_id.toString() }
      })
    } else {
      router.push(`/poems/${randomPoem.value.id}`)
    }
  }
}

// 组件挂载时加载随机诗词并启动倒计时
onMounted(() => {
  fetchRandomPoem().then(() => {
    startCountdown()
  })
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopCountdown()
})
</script>

<template>
  <div class="quote-card" @click="goToDetail">
    <!-- 装饰性引号 -->
    <div class="quote-mark quote-mark-open">「</div>
    <div class="quote-mark quote-mark-close">」</div>
    
    <!-- 刷新按钮 -->
    <button 
      class="refresh-btn"
      :class="{ 'is-loading': isLoading }"
      @click.stop="refreshRandomPoem"
      :disabled="isLoading"
    >
      <RefreshOutline class="refresh-icon" />
    </button>

    <!-- 加载状态 -->
    <div v-if="isLoading && !randomPoem" class="loading-container">
      <NSpin size="small" />
      <span class="loading-text">加载中</span>
    </div>

    <!-- 诗词内容 -->
    <div v-else-if="randomPoem" class="quote-content">
      <div class="quote-sentences">
        <p 
          v-for="(sentence, index) in displayedSentences" 
          :key="index"
          class="sentence"
          :style="{ animationDelay: `${index * 0.15}s` }"
        >
          {{ sentence }}
        </p>
      </div>
      
      <div class="quote-meta">
        <div class="meta-left">
          <DynastyBadge :dynasty="randomPoem.dynasty" size="small" />
          <span class="author-name">{{ randomPoem.author }}</span>
        </div>
        <span class="poem-title">《{{ randomPoem.title || '无题' }}》</span>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <p>暂无数据</p>
      <button class="retry-btn" @click.stop="fetchRandomPoem">重试</button>
    </div>

    <!-- 倒计时进度条 -->
    <div class="countdown-bar">
      <div class="countdown-progress" :style="{ width: `${countdownProgress}%` }"></div>
    </div>

    <!-- 倒计时显示 -->
    <div class="countdown-display">
      <span class="countdown-text">{{ countdown }}</span>
      <span class="countdown-label">秒后刷新</span>
    </div>
  </div>
</template>

<style scoped>
.quote-card {
  position: relative;
  padding: 24px 20px 28px;
  background: linear-gradient(
    165deg,
    rgba(139, 38, 53, 0.03) 0%,
    rgba(201, 169, 110, 0.02) 50%,
    rgba(139, 38, 53, 0.03) 100%
  );
  border: 1px solid rgba(139, 38, 53, 0.12);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  width: 100%;
}

.quote-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(139, 38, 53, 0.4) 20%,
    rgba(201, 169, 110, 0.5) 50%,
    rgba(139, 38, 53, 0.4) 80%,
    transparent 100%
  );
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

.quote-card:hover {
  border-color: rgba(139, 38, 53, 0.2);
  background: linear-gradient(
    165deg,
    rgba(139, 38, 53, 0.05) 0%,
    rgba(201, 169, 110, 0.03) 50%,
    rgba(139, 38, 53, 0.05) 100%
  );
  transform: translateY(-2px);
  box-shadow: 
    0 8px 32px rgba(139, 38, 53, 0.06),
    0 2px 8px rgba(139, 38, 53, 0.04);
}

.quote-card:hover::before {
  opacity: 1;
}

/* 装饰性引号 */
.quote-mark {
  position: absolute;
  font-family: "Noto Serif SC", "SimSun", serif;
  font-size: 48px;
  color: rgba(139, 38, 53, 0.1);
  line-height: 1;
  pointer-events: none;
  user-select: none;
  transition: all 0.4s ease;
}

.quote-mark-open {
  top: 4px;
  left: 12px;
}

.quote-mark-close {
  bottom: 36px;
  right: 12px;
}

.quote-card:hover .quote-mark {
  color: rgba(139, 38, 53, 0.18);
}

.quote-card:hover .quote-mark-open {
  transform: translateX(-4px);
}

.quote-card:hover .quote-mark-close {
  transform: translateX(4px);
}

/* 刷新按钮 */
.refresh-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(139, 38, 53, 0.15);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(139, 38, 53, 0.5);
  z-index: 10;
}

.refresh-btn:hover {
  background: rgba(139, 38, 53, 0.06);
  border-color: rgba(139, 38, 53, 0.25);
  color: rgba(139, 38, 53, 0.8);
  transform: rotate(180deg);
}

.refresh-btn.is-loading .refresh-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.refresh-icon {
  width: 16px;
  height: 16px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  gap: 8px;
}

.loading-text {
  font-size: 13px;
  color: var(--color-ink-light);
  letter-spacing: 2px;
}

/* 引用内容 */
.quote-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quote-sentences {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 0 24px;
  flex-wrap: wrap;
}

.sentence {
  font-family: "Noto Serif SC", "SimSun", serif;
  font-size: 17px;
  font-weight: 500;
  color: var(--color-ink);
  line-height: 1.6;
  text-align: center;
  margin: 0;
  opacity: 0;
  transform: translateY(10px);
  animation: fadeInUp 0.5s ease forwards;
  white-space: nowrap;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 元信息 */
.quote-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid rgba(139, 38, 53, 0.08);
}

.meta-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.author-name {
  font-size: 14px;
  color: var(--color-ink);
  font-weight: 500;
}

.poem-title {
  font-size: 13px;
  color: var(--color-ink-light);
  font-style: italic;
}

/* 倒计时进度条 */
.countdown-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(139, 38, 53, 0.06);
  overflow: hidden;
}

.countdown-progress {
  height: 100%;
  background: linear-gradient(
    90deg,
    rgba(139, 38, 53, 0.2),
    rgba(201, 169, 110, 0.6),
    rgba(139, 38, 53, 0.2)
  );
  box-shadow: 0 0 6px rgba(201, 169, 110, 0.3);
  transition: width 0.1s linear;
}

/* 倒计时显示 */
.countdown-display {
  position: absolute;
  bottom: 8px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(139, 38, 53, 0.04);
  border: 1px solid rgba(139, 38, 53, 0.1);
  border-radius: 12px;
  font-size: 12px;
  color: rgba(139, 38, 53, 0.5);
  font-family: "Noto Serif SC", serif;
  transition: all 0.3s ease;
}

.quote-card:hover .countdown-display {
  background: rgba(139, 38, 53, 0.08);
  border-color: rgba(139, 38, 53, 0.15);
  color: rgba(139, 38, 53, 0.7);
}

.countdown-text {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.countdown-label {
  font-size: 10px;
  opacity: 0.7;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 20px;
  gap: 12px;
  color: var(--color-ink-light);
}

.empty-state p {
  font-size: 14px;
  margin: 0;
}

.retry-btn {
  padding: 8px 20px;
  font-size: 13px;
  color: var(--color-seal);
  background: transparent;
  border: 1px solid rgba(139, 38, 53, 0.2);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  background: rgba(139, 38, 53, 0.06);
  border-color: rgba(139, 38, 53, 0.3);
}

/* 响应式 */
@media (max-width: 768px) {
  .quote-card {
    padding: 20px 16px 24px;
  }

  .quote-mark {
    font-size: 36px;
  }

  .quote-mark-open {
    top: 2px;
    left: 8px;
  }

  .quote-mark-close {
    bottom: 32px;
    right: 8px;
  }

  .sentence {
    font-size: 15px;
    padding: 0 4px;
  }

  .quote-meta {
    flex-direction: column;
    gap: 6px;
    align-items: center;
  }

  .quote-sentences {
    padding: 0 16px;
  }
}
</style>
