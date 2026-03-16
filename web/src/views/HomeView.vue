<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { BookOutline, PeopleOutline, GitNetworkOutline, SearchOutline, FlameOutline, CloudOutline, ReaderOutline, BarChartOutline } from '@vicons/ionicons5'

import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'

const router = useRouter()

const poemsV2 = usePoemsV2()
const authorsV2 = useAuthorsV2()
const wordSimilarityV2 = useWordSimilarityV2()

const loading = ref(true)
const loadedCount = ref(0)
const totalToLoad = 3
const animationStarted = ref(false)

const checkLoadComplete = () => {
  loadedCount.value++
  if (loadedCount.value >= totalToLoad) {
    loading.value = false
    setTimeout(() => {
      animationStarted.value = true
    }, 100)
  }
}

const loadAllData = async () => {
  loading.value = true
  loadedCount.value = 0
  animationStarted.value = false

  await poemsV2.loadMetadata()
  checkLoadComplete()

  await authorsV2.loadMetadata()
  checkLoadComplete()

  await wordSimilarityV2.loadMetadata()
  checkLoadComplete()
}

onMounted(() => {
  loadAllData()
})

const formatNumber = (num: number | undefined | null): string => {
  if (num === undefined || num === null) return '--'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

// 数字滚动动画
const animatedNumbers = ref({
  authors: 0,
  poems: 0,
  vocab: 0
})

const animateNumber = (target: number, key: 'authors' | 'poems' | 'vocab', duration: number = 1500) => {
  const start = 0
  const startTime = performance.now()

  const updateNumber = (currentTime: number) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easeOutQuart = 1 - Math.pow(1 - progress, 4)
    animatedNumbers.value[key] = Math.floor(start + (target - start) * easeOutQuart)

    if (progress < 1) {
      requestAnimationFrame(updateNumber)
    }
  }

  requestAnimationFrame(updateNumber)
}

watch(() => animationStarted.value, (started) => {
  if (started) {
    setTimeout(() => animateNumber(authorsV2.totalAuthors.value || 0, 'authors'), 800)
    setTimeout(() => animateNumber(poemsV2.totalPoems.value || 0, 'poems', 1800), 1000)
    setTimeout(() => animateNumber(wordSimilarityV2.vocabSize.value || 0, 'vocab', 1200), 1200)
  }
})
</script>

<template>
  <div class="home-view" :class="{ 'animate-in': animationStarted }">
    <section class="hero-section">
      <!-- 动态背景层 -->
      <div class="hero-bg">
        <div class="bg-gradient"></div>
        <div class="bg-texture"></div>
      </div>

      <!-- 四角榫卯装饰 - 真正的凹凸咬合结构 -->
      <div class="sunmao-ornament sunmao-tl">
        <svg viewBox="0 0 100 100" class="sunmao-svg">
          <!-- 横向木构件 -->
          <path class="sunmao-wood-h" d="M0 25 L45 25 L45 20 L55 20 L55 25 L100 25 L100 45 L55 45 L55 50 L45 50 L45 45 L0 45 Z" />
          <!-- 纵向木构件 -->
          <path class="sunmao-wood-v" d="M25 0 L25 45 L20 45 L20 55 L25 55 L25 100 L45 100 L45 55 L50 55 L50 45 L45 45 L45 0 Z" />
          <!-- 榫头（阳）- 横向伸出 -->
          <rect class="sunmao-tenon" x="42" y="28" width="16" height="14" rx="1" />
          <!-- 卯眼（阴）- 纵向挖去 -->
          <path class="sunmao-mortise" d="M28 42 L42 42 L42 28 L28 28 Z" />
          <!-- 咬合缝隙 -->
          <line class="sunmao-gap" x1="45" y1="25" x2="45" y2="45" />
          <line class="sunmao-gap" x1="25" y1="45" x2="45" y2="45" />
          <!-- 木纹细节 -->
          <line class="sunmao-grain" x1="10" y1="32" x2="35" y2="32" />
          <line class="sunmao-grain" x1="10" y1="38" x2="35" y2="38" />
          <line class="sunmao-grain" x1="32" y1="10" x2="32" y2="35" />
          <line class="sunmao-grain" x1="38" y1="10" x2="38" y2="35" />
          <!-- 中心锁定点 -->
          <circle class="sunmao-lock" cx="35" cy="35" r="4" />
        </svg>
      </div>
      <div class="sunmao-ornament sunmao-tr">
        <svg viewBox="0 0 100 100" class="sunmao-svg">
          <!-- 横向木构件 -->
          <path class="sunmao-wood-h" d="M0 25 L45 25 L45 20 L55 20 L55 25 L100 25 L100 45 L55 45 L55 50 L45 50 L45 45 L0 45 Z" />
          <!-- 纵向木构件 -->
          <path class="sunmao-wood-v" d="M55 0 L55 45 L50 45 L50 55 L55 55 L55 100 L75 100 L75 55 L80 55 L80 45 L75 45 L75 0 Z" />
          <!-- 榫头 -->
          <rect class="sunmao-tenon" x="42" y="28" width="16" height="14" rx="1" />
          <!-- 卯眼 -->
          <path class="sunmao-mortise" d="M58 42 L72 42 L72 28 L58 28 Z" />
          <!-- 咬合缝隙 -->
          <line class="sunmao-gap" x1="55" y1="25" x2="55" y2="45" />
          <line class="sunmao-gap" x1="55" y1="45" x2="75" y2="45" />
          <!-- 木纹 -->
          <line class="sunmao-grain" x1="65" y1="32" x2="90" y2="32" />
          <line class="sunmao-grain" x1="65" y1="38" x2="90" y2="38" />
          <line class="sunmao-grain" x1="62" y1="10" x2="62" y2="35" />
          <line class="sunmao-grain" x1="68" y1="10" x2="68" y2="35" />
          <!-- 锁定点 -->
          <circle class="sunmao-lock" cx="65" cy="35" r="4" />
        </svg>
      </div>
      <div class="sunmao-ornament sunmao-bl">
        <svg viewBox="0 0 100 100" class="sunmao-svg">
          <!-- 横向木构件 -->
          <path class="sunmao-wood-h" d="M0 55 L45 55 L45 50 L55 50 L55 55 L100 55 L100 75 L55 75 L55 80 L45 80 L45 75 L0 75 Z" />
          <!-- 纵向木构件 -->
          <path class="sunmao-wood-v" d="M25 0 L25 45 L20 45 L20 55 L25 55 L25 100 L45 100 L45 55 L50 55 L50 45 L45 45 L45 0 Z" />
          <!-- 榫头 -->
          <rect class="sunmao-tenon" x="42" y="58" width="16" height="14" rx="1" />
          <!-- 卯眼 -->
          <path class="sunmao-mortise" d="M28 72 L42 72 L42 58 L28 58 Z" />
          <!-- 咬合缝隙 -->
          <line class="sunmao-gap" x1="45" y1="55" x2="45" y2="75" />
          <line class="sunmao-gap" x1="25" y1="55" x2="45" y2="55" />
          <!-- 木纹 -->
          <line class="sunmao-grain" x1="10" y1="62" x2="35" y2="62" />
          <line class="sunmao-grain" x1="10" y1="68" x2="35" y2="68" />
          <line class="sunmao-grain" x1="32" y1="65" x2="32" y2="90" />
          <line class="sunmao-grain" x1="38" y1="65" x2="38" y2="90" />
          <!-- 锁定点 -->
          <circle class="sunmao-lock" cx="35" cy="65" r="4" />
        </svg>
      </div>
      <div class="sunmao-ornament sunmao-br">
        <svg viewBox="0 0 100 100" class="sunmao-svg">
          <!-- 横向木构件 -->
          <path class="sunmao-wood-h" d="M0 55 L45 55 L45 50 L55 50 L55 55 L100 55 L100 75 L55 75 L55 80 L45 80 L45 75 L0 75 Z" />
          <!-- 纵向木构件 -->
          <path class="sunmao-wood-v" d="M55 0 L55 45 L50 45 L50 55 L55 55 L55 100 L75 100 L75 55 L80 55 L80 45 L75 45 L75 0 Z" />
          <!-- 榫头 -->
          <rect class="sunmao-tenon" x="42" y="58" width="16" height="14" rx="1" />
          <!-- 卯眼 -->
          <path class="sunmao-mortise" d="M58 72 L72 72 L72 58 L58 58 Z" />
          <!-- 咬合缝隙 -->
          <line class="sunmao-gap" x1="55" y1="55" x2="55" y2="75" />
          <line class="sunmao-gap" x1="55" y1="55" x2="75" y2="55" />
          <!-- 木纹 -->
          <line class="sunmao-grain" x1="65" y1="62" x2="90" y2="62" />
          <line class="sunmao-grain" x1="65" y1="68" x2="90" y2="68" />
          <line class="sunmao-grain" x1="62" y1="65" x2="62" y2="90" />
          <line class="sunmao-grain" x1="68" y1="65" x2="68" y2="90" />
          <!-- 锁定点 -->
          <circle class="sunmao-lock" cx="65" cy="65" r="4" />
        </svg>
      </div>

      <!-- 边框呼吸线 -->
      <div class="frame-line frame-top"></div>
      <div class="frame-line frame-bottom"></div>
      <div class="frame-line frame-left"></div>
      <div class="frame-line frame-right"></div>

      <!-- 主内容 -->
      <div class="hero-content">
        <!-- 时间感知问候 -->
        <div class="time-greeting">
          <span class="greeting-text" id="greeting">寻诗者</span>
          <span class="greeting-divider"></span>
          <span class="greeting-sub">今日可有所得</span>
        </div>

        <!-- 主标题 -->
        <div class="title-block">
          <span class="title-zh" v-for="(char, i) in ['文', '脉', '千', '秋']" :key="i" :style="{ animationDelay: `${0.3 + i * 0.12}s` }">
            {{ char }}
          </span>
        </div>

        <!-- 副标题 -->
        <h1 class="hero-title">
          <span class="title-main">数字诗学图谱</span>
        </h1>

        <!-- 描述语 -->
        <p class="hero-subtitle">
          <span class="subtitle-line">三十三万首诗词</span>
          <span class="subtitle-divider"></span>
          <span class="subtitle-line">待君采撷</span>
        </p>
      </div>
    </section>

    <!-- 数据统计卡片 -->
    <section class="stats-section">
      <div class="stats-grid">
        <div class="stat-card" :style="{ animationDelay: '0.8s' }">
          <div class="stat-icon-wrap">
            <PeopleOutline class="stat-icon" />
          </div>
          <div class="stat-content">
            <span class="stat-number">{{ formatNumber(animatedNumbers.authors) }}</span>
            <span class="stat-label">位诗人</span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" :style="{ animationDelay: '0.95s' }">
          <div class="stat-icon-wrap">
            <BookOutline class="stat-icon" />
          </div>
          <div class="stat-content">
            <span class="stat-number">{{ formatNumber(animatedNumbers.poems) }}</span>
            <span class="stat-label">首诗词</span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" :style="{ animationDelay: '1.1s' }">
          <div class="stat-icon-wrap">
            <GitNetworkOutline class="stat-icon" />
          </div>
          <div class="stat-content">
            <span class="stat-number">{{ formatNumber(animatedNumbers.vocab) }}</span>
            <span class="stat-label">个词条</span>
          </div>
          <div class="stat-glow"></div>
        </div>
      </div>
    </section>

    <!-- 简介区域 -->
    <section class="intro-section">
      <div class="intro-frame" :style="{ animationDelay: '1.3s' }">
        <div class="frame-corner tl"></div>
        <div class="frame-corner tr"></div>
        <div class="frame-corner bl"></div>
        <div class="frame-corner br"></div>
        <div class="intro-content">
          <p class="intro-text">
            基于 <a href="https://github.com/chinese-poetry/chinese-poetry" target="_blank" class="intro-link">chinese-poetry</a>
            开源数据库构建，收录<strong>全唐诗</strong>、<strong>全宋诗</strong>、<strong>全宋词</strong>三大诗词宝库。
            提供词频分析、相似度分析等可视化挖掘功能，让千年文脉在数据中流转。
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 32px;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 24px;
}

/* ===== Hero Section ===== */
.hero-section {
  position: relative;
  padding: 48px 40px 40px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

/* 动态背景 */
.hero-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  opacity: 0;
  transition: opacity 1s ease 0.2s;
}

.animate-in .hero-bg {
  opacity: 1;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% 0%, rgba(139, 38, 53, 0.04) 0%, transparent 70%),
    radial-gradient(ellipse 60% 40% at 80% 100%, rgba(201, 169, 110, 0.06) 0%, transparent 60%);
}

.bg-texture {
  position: absolute;
  inset: 0;
  background-image:
    repeating-linear-gradient(90deg, transparent, transparent 60px, rgba(139, 38, 53, 0.015) 60px, rgba(139, 38, 53, 0.015) 61px),
    repeating-linear-gradient(0deg, transparent, transparent 60px, rgba(139, 38, 53, 0.015) 60px, rgba(139, 38, 53, 0.015) 61px);
  opacity: 0.5;
}

/* 四角榫卯装饰 - 真正的凹凸咬合结构 */
.sunmao-ornament {
  position: absolute;
  width: 80px;
  height: 80px;
  opacity: 0;
}

.animate-in .sunmao-ornament {
  animation: woodSlideIn 1s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.sunmao-ornament.sunmao-tl {
  top: 8px;
  left: 8px;
  animation-delay: 0.2s;
}

.sunmao-ornament.sunmao-tr {
  top: 8px;
  right: 8px;
  animation-delay: 0.35s;
}

.sunmao-ornament.sunmao-bl {
  bottom: 8px;
  left: 8px;
  animation-delay: 0.5s;
}

.sunmao-ornament.sunmao-br {
  bottom: 8px;
  right: 8px;
  animation-delay: 0.65s;
}

.sunmao-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* 横向木构件 - 从左侧飞入 */
.sunmao-wood-h {
  fill: rgba(139, 38, 53, 0.12);
  stroke: var(--color-seal);
  stroke-width: 2;
  stroke-linejoin: round;
  opacity: 0;
}

.animate-in .sunmao-tl .sunmao-wood-h {
  animation: woodHSlideFromLeft 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.3s;
}

.animate-in .sunmao-tr .sunmao-wood-h {
  animation: woodHSlideFromRight 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.45s;
}

.animate-in .sunmao-bl .sunmao-wood-h {
  animation: woodHSlideFromLeft 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.6s;
}

.animate-in .sunmao-br .sunmao-wood-h {
  animation: woodHSlideFromRight 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.75s;
}

/* 纵向木构件 - 从上方飞入 */
.sunmao-wood-v {
  fill: rgba(139, 38, 53, 0.08);
  stroke: var(--color-seal);
  stroke-width: 2;
  stroke-linejoin: round;
  opacity: 0;
}

.animate-in .sunmao-tl .sunmao-wood-v {
  animation: woodVSlideFromTop 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.5s;
}

.animate-in .sunmao-tr .sunmao-wood-v {
  animation: woodVSlideFromTop 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.65s;
}

.animate-in .sunmao-bl .sunmao-wood-v {
  animation: woodVSlideFromBottom 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.8s;
}

.animate-in .sunmao-br .sunmao-wood-v {
  animation: woodVSlideFromBottom 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.95s;
}

/* 榫头 - 凸起部分 */
.sunmao-tenon {
  fill: var(--color-seal);
  opacity: 0;
  transform-origin: center;
}

.animate-in .sunmao-tenon {
  animation: tenonFit 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.sunmao-tl .sunmao-tenon { animation-delay: 0.7s; }
.sunmao-tr .sunmao-tenon { animation-delay: 0.85s; }
.sunmao-bl .sunmao-tenon { animation-delay: 1s; }
.sunmao-br .sunmao-tenon { animation-delay: 1.15s; }

/* 卯眼 - 挖去部分（用浅色表示凹陷） */
.sunmao-mortise {
  fill: var(--color-bg);
  stroke: var(--color-seal);
  stroke-width: 1.5;
  opacity: 0;
}

.animate-in .sunmao-mortise {
  animation: mortiseReveal 0.4s ease forwards;
}

.sunmao-tl .sunmao-mortise { animation-delay: 0.9s; }
.sunmao-tr .sunmao-mortise { animation-delay: 1.05s; }
.sunmao-bl .sunmao-mortise { animation-delay: 1.2s; }
.sunmao-br .sunmao-mortise { animation-delay: 1.35s; }

/* 咬合缝隙 */
.sunmao-gap {
  stroke: var(--color-accent);
  stroke-width: 1;
  stroke-dasharray: 4 2;
  opacity: 0;
}

.animate-in .sunmao-gap {
  animation: gapShow 0.3s ease forwards;
}

.sunmao-tl .sunmao-gap { animation-delay: 1.1s; }
.sunmao-tr .sunmao-gap { animation-delay: 1.25s; }
.sunmao-bl .sunmao-gap { animation-delay: 1.4s; }
.sunmao-br .sunmao-gap { animation-delay: 1.55s; }

/* 木纹 */
.sunmao-grain {
  stroke: rgba(139, 38, 53, 0.2);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0;
}

.animate-in .sunmao-grain {
  animation: grainAppear 0.4s ease forwards;
}

.sunmao-tl .sunmao-grain:nth-of-type(1) { animation-delay: 1.2s; }
.sunmao-tl .sunmao-grain:nth-of-type(2) { animation-delay: 1.25s; }
.sunmao-tl .sunmao-grain:nth-of-type(3) { animation-delay: 1.3s; }
.sunmao-tl .sunmao-grain:nth-of-type(4) { animation-delay: 1.35s; }
.sunmao-tr .sunmao-grain:nth-of-type(1) { animation-delay: 1.35s; }
.sunmao-tr .sunmao-grain:nth-of-type(2) { animation-delay: 1.4s; }
.sunmao-tr .sunmao-grain:nth-of-type(3) { animation-delay: 1.45s; }
.sunmao-tr .sunmao-grain:nth-of-type(4) { animation-delay: 1.5s; }
.sunmao-bl .sunmao-grain:nth-of-type(1) { animation-delay: 1.5s; }
.sunmao-bl .sunmao-grain:nth-of-type(2) { animation-delay: 1.55s; }
.sunmao-bl .sunmao-grain:nth-of-type(3) { animation-delay: 1.6s; }
.sunmao-bl .sunmao-grain:nth-of-type(4) { animation-delay: 1.65s; }
.sunmao-br .sunmao-grain:nth-of-type(1) { animation-delay: 1.65s; }
.sunmao-br .sunmao-grain:nth-of-type(2) { animation-delay: 1.7s; }
.sunmao-br .sunmao-grain:nth-of-type(3) { animation-delay: 1.75s; }
.sunmao-br .sunmao-grain:nth-of-type(4) { animation-delay: 1.8s; }

/* 锁定点 */
.sunmao-lock {
  fill: var(--color-accent);
  stroke: var(--color-seal);
  stroke-width: 1;
  opacity: 0;
  transform-origin: center;
}

.animate-in .sunmao-lock {
  animation: lockPin 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.sunmao-tl .sunmao-lock { animation-delay: 1.4s; }
.sunmao-tr .sunmao-lock { animation-delay: 1.55s; }
.sunmao-bl .sunmao-lock { animation-delay: 1.7s; }
.sunmao-br .sunmao-lock { animation-delay: 1.85s; }

/* 动画关键帧 */
@keyframes woodSlideIn {
  0% {
    opacity: 0;
    transform: translate(-20px, -20px) scale(0.8);
  }
  100% {
    opacity: 1;
    transform: translate(0, 0) scale(1);
  }
}

/* 横向木构件飞入动画 */
@keyframes woodHSlideFromLeft {
  0% {
    opacity: 0;
    transform: translateX(-60px) rotate(-5deg);
  }
  60% {
    opacity: 1;
    transform: translateX(5px) rotate(1deg);
  }
  100% {
    opacity: 1;
    transform: translateX(0) rotate(0);
  }
}

@keyframes woodHSlideFromRight {
  0% {
    opacity: 0;
    transform: translateX(60px) rotate(5deg);
  }
  60% {
    opacity: 1;
    transform: translateX(-5px) rotate(-1deg);
  }
  100% {
    opacity: 1;
    transform: translateX(0) rotate(0);
  }
}

/* 纵向木构件飞入动画 */
@keyframes woodVSlideFromTop {
  0% {
    opacity: 0;
    transform: translateY(-60px) rotate(5deg);
  }
  60% {
    opacity: 1;
    transform: translateY(5px) rotate(-1deg);
  }
  100% {
    opacity: 1;
    transform: translateY(0) rotate(0);
  }
}

@keyframes woodVSlideFromBottom {
  0% {
    opacity: 0;
    transform: translateY(60px) rotate(-5deg);
  }
  60% {
    opacity: 1;
    transform: translateY(-5px) rotate(1deg);
  }
  100% {
    opacity: 1;
    transform: translateY(0) rotate(0);
  }
}

@keyframes tenonFit {
  0% {
    opacity: 0;
    transform: scale(0.3) translateY(-10px);
  }
  60% {
    opacity: 1;
    transform: scale(1.1) translateY(2px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes mortiseReveal {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes gapShow {
  to { opacity: 0.6; }
}

@keyframes grainAppear {
  to { opacity: 1; }
}

@keyframes lockPin {
  0% {
    opacity: 0;
    transform: scale(0) rotate(-45deg);
  }
  50% {
    opacity: 1;
    transform: scale(1.3) rotate(10deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0);
  }
}

/* 边框呼吸线 */
.frame-line {
  position: absolute;
  background: var(--color-border);
  opacity: 0;
}

.animate-in .frame-line {
  opacity: 0.5;
  animation: frameBreathe 5s ease-in-out infinite;
}

.frame-top {
  top: 28px;
  left: 80px;
  right: 80px;
  height: 1px;
  animation-delay: 0.3s;
}

.frame-bottom {
  bottom: 28px;
  left: 80px;
  right: 80px;
  height: 1px;
  animation-delay: 0.5s;
}

.frame-left {
  left: 28px;
  top: 80px;
  bottom: 80px;
  width: 1px;
  animation-delay: 0.4s;
}

.frame-right {
  right: 28px;
  top: 80px;
  bottom: 80px;
  width: 1px;
  animation-delay: 0.6s;
}

@keyframes frameBreathe {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

/* Hero 内容 */
.hero-content {
  position: relative;
  z-index: 10;
  text-align: center;
}

/* 时间感知问候 */
.time-greeting {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  opacity: 0;
  transform: translateY(-10px);
}

.animate-in .time-greeting {
  animation: fadeInDown 0.6s ease forwards;
  animation-delay: 0.1s;
}

.greeting-text {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  color: var(--color-seal);
  letter-spacing: 3px;
  font-weight: 600;
  padding: 6px 14px;
  background: linear-gradient(135deg, rgba(139, 38, 53, 0.08) 0%, rgba(139, 38, 53, 0.03) 100%);
  border: 1px solid rgba(139, 38, 53, 0.2);
  border-radius: 4px;
}

.greeting-divider {
  width: 20px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-accent), transparent);
}

.greeting-sub {
  font-size: 13px;
  color: var(--color-ink-light);
  letter-spacing: 2px;
  font-style: italic;
}

.title-block {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.title-zh {
  font-family: "Noto Serif SC", serif;
  font-size: 42px;
  font-weight: 700;
  color: var(--color-seal);
  opacity: 0;
  transform: translateY(-30px) rotate(-8deg);
  display: inline-block;
}

.animate-in .title-zh {
  animation: titleCharIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes titleCharIn {
  from {
    opacity: 0;
    transform: translateY(-30px) rotate(-8deg) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translateY(0) rotate(0) scale(1);
  }
}

.hero-title {
  margin: 0 0 20px;
}

.title-main {
  font-family: "Noto Serif SC", serif;
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: 12px;
  opacity: 0;
  display: inline-block;
}

.animate-in .title-main {
  animation: fadeInUp 0.7s ease forwards;
  animation-delay: 0.75s;
}

.hero-subtitle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-family: "Noto Serif SC", serif;
  font-size: 16px;
  color: var(--color-ink-light);
  margin: 0;
  opacity: 0;
}

.animate-in .hero-subtitle {
  animation: fadeInUp 0.7s ease forwards;
  animation-delay: 0.9s;
}

.subtitle-divider {
  width: 24px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-accent), transparent);
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== Stats Section ===== */
.stats-section {
  padding: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  position: relative;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.3s ease;
}

.animate-in .stat-card {
  animation: cardSlideUp 0.6s ease forwards;
}

@keyframes cardSlideUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card:hover {
  border-color: var(--color-seal);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(139, 38, 53, 0.1);
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, rgba(139, 38, 53, 0.08) 0%, rgba(139, 38, 53, 0.02) 100%);
  border: 1px solid rgba(139, 38, 53, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover .stat-icon-wrap {
  background: linear-gradient(135deg, var(--color-seal) 0%, #A83246 100%);
  border-color: transparent;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(139, 38, 53, 0.25);
}

.stat-icon {
  width: 24px;
  height: 24px;
  color: var(--color-seal);
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  color: white;
  transform: scale(1.1);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-number {
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-seal);
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--color-ink-light);
  letter-spacing: 1px;
}

.stat-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(139, 38, 53, 0.08) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover .stat-glow {
  opacity: 1;
}

/* ===== Intro Section ===== */
.intro-section {
  padding: 0;
}

.intro-frame {
  position: relative;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  padding: 28px 32px;
  opacity: 0;
  transform: scale(0.98);
}

.animate-in .intro-frame {
  animation: frameScaleIn 0.6s ease forwards;
  animation-delay: 1.3s;
}

@keyframes frameScaleIn {
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.frame-corner {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid var(--color-accent);
  opacity: 0;
}

.animate-in .frame-corner {
  animation: cornerFadeIn 0.4s ease forwards;
  animation-delay: 1.6s;
}

@keyframes cornerFadeIn {
  to { opacity: 1; }
}

.frame-corner.tl { top: -1px; left: -1px; border-right: none; border-bottom: none; }
.frame-corner.tr { top: -1px; right: -1px; border-left: none; border-bottom: none; }
.frame-corner.bl { bottom: -1px; left: -1px; border-right: none; border-top: none; }
.frame-corner.br { bottom: -1px; right: -1px; border-left: none; border-top: none; }

.intro-text {
  font-size: 14px;
  line-height: 1.9;
  color: var(--color-ink);
  text-align: center;
  margin: 0;
}

.intro-text strong {
  color: var(--color-seal);
  font-weight: 600;
  position: relative;
}

.intro-link {
  color: var(--color-seal);
  text-decoration: none;
  position: relative;
  font-weight: 500;
}

.intro-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--color-seal);
  transition: width 0.3s ease;
}

.intro-link:hover::after {
  width: 100%;
}

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .home-view {
    padding: 20px 24px;
    gap: 20px;
  }

  .hero-section {
    padding: 40px 32px 32px;
  }

  .title-zh {
    font-size: 36px;
  }

  .title-main {
    font-size: 24px;
    letter-spacing: 8px;
  }

  .stats-grid {
    gap: 16px;
  }

  .stat-card {
    padding: 20px 16px;
  }

  .stat-icon-wrap {
    width: 40px;
    height: 40px;
  }

  .stat-icon {
    width: 20px;
    height: 20px;
  }

  .stat-number {
    font-size: 20px;
  }
}

@media (max-width: 768px) {
  .home-view {
    padding: 16px;
    gap: 16px;
    min-height: auto;
  }

  .hero-section {
    padding: 32px 20px 28px;
  }

  .hero-frame {
    width: 24px;
    height: 24px;
  }

  .brand-badge {
    margin-bottom: 16px;
  }

  .title-block {
    gap: 8px;
    margin-bottom: 12px;
  }

  .title-zh {
    font-size: 32px;
  }

  .hero-title {
    margin-bottom: 16px;
  }

  .title-main {
    font-size: 20px;
    letter-spacing: 6px;
  }

  .hero-subtitle {
    flex-direction: column;
    gap: 8px;
    font-size: 14px;
  }

  .subtitle-divider {
    width: 40px;
    height: 1px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .stat-card {
    padding: 16px 20px;
    flex-direction: row;
    justify-content: flex-start;
  }

  .stat-content {
    flex-direction: row;
    align-items: baseline;
    gap: 8px;
  }

  .intro-frame {
    padding: 24px 20px;
  }

  .intro-text {
    font-size: 13px;
    line-height: 1.8;
  }
}

@media (max-width: 480px) {
  .title-zh {
    font-size: 28px;
  }

  .title-main {
    font-size: 18px;
    letter-spacing: 4px;
  }
}
</style>
