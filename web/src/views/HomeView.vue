<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { BookOutline, PeopleOutline, GitNetworkOutline, SearchOutline, FlameOutline, CloudOutline, ReaderOutline, BarChartOutline } from '@vicons/ionicons5'

import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { useLoading } from '@/composables/useLoading'

const router = useRouter()
const loading = useLoading()

const poemsV2 = usePoemsV2()
const authorsV2 = useAuthorsV2()
const wordSimilarityV2 = useWordSimilarityV2()

const animationStarted = ref(false)

const loadAllData = async () => {
  animationStarted.value = false

  const taskId = loading.startBlocking(
    '文脉初启',
    '正在加载诗词数据...',
    10
  )

  try {
    loading.update(taskId, { description: '正在加载诗词元数据...', progress: 10 })
    await poemsV2.loadMetadata()
    loading.update(taskId, { description: '正在加载诗人数据...', progress: 40 })

    await authorsV2.loadMetadata()
    loading.update(taskId, { description: '正在加载词频数据...', progress: 70 })

    await wordSimilarityV2.loadMetadata()
    loading.update(taskId, { description: '数据加载完成', progress: 100 })

    setTimeout(() => {
      loading.finish(taskId)
      setTimeout(() => {
        animationStarted.value = true
      }, 100)
    }, 300)
  } catch (error) {
    loading.update(taskId, { description: '加载失败，请刷新重试' })
    console.error('数据加载失败:', error)
  }
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

          <!-- 四角榫卯装饰 - 十字交叉直榫结构 -->
      <div class="sunmao-ornament sunmao-tl">
        <svg viewBox="0 0 100 100" class="sunmao-svg" preserveAspectRatio="xMidYMid meet">
          <!-- 横向木杆 -->
          <rect class="sunmao-beam-h" x="0" y="32" width="56" height="8" />
          <!-- 纵向木杆 -->
          <rect class="sunmao-beam-v" x="32" y="0" width="8" height="56" />
          <!-- 中心咬合区 -->
          <rect class="sunmao-joint" x="32" y="32" width="8" height="8" />
          <!-- 榫头凸起 -->
          <rect class="sunmao-tenon" x="30" y="34" width="2" height="4" />
          <rect class="sunmao-tenon" x="40" y="34" width="2" height="4" />
          <rect class="sunmao-tenon" x="34" y="30" width="4" height="2" />
          <rect class="sunmao-tenon" x="34" y="40" width="4" height="2" />
        </svg>
      </div>
      <div class="sunmao-ornament sunmao-tr">
        <svg viewBox="0 0 100 100" class="sunmao-svg" preserveAspectRatio="xMidYMid meet">
          <!-- 横向木杆 -->
          <rect class="sunmao-beam-h" x="44" y="32" width="56" height="8" />
          <!-- 纵向木杆 -->
          <rect class="sunmao-beam-v" x="60" y="0" width="8" height="56" />
          <!-- 中心咬合区 -->
          <rect class="sunmao-joint" x="60" y="32" width="8" height="8" />
          <!-- 榫头凸起 -->
          <rect class="sunmao-tenon" x="58" y="34" width="2" height="4" />
          <rect class="sunmao-tenon" x="68" y="34" width="2" height="4" />
          <rect class="sunmao-tenon" x="62" y="30" width="4" height="2" />
          <rect class="sunmao-tenon" x="62" y="40" width="4" height="2" />
        </svg>
      </div>
      <div class="sunmao-ornament sunmao-bl">
        <svg viewBox="0 0 100 100" class="sunmao-svg" preserveAspectRatio="xMidYMid meet">
          <!-- 横向木杆 -->
          <rect class="sunmao-beam-h" x="0" y="60" width="56" height="8" />
          <!-- 纵向木杆 -->
          <rect class="sunmao-beam-v" x="32" y="44" width="8" height="56" />
          <!-- 中心咬合区 -->
          <rect class="sunmao-joint" x="32" y="60" width="8" height="8" />
          <!-- 榫头凸起 -->
          <rect class="sunmao-tenon" x="30" y="62" width="2" height="4" />
          <rect class="sunmao-tenon" x="40" y="62" width="2" height="4" />
          <rect class="sunmao-tenon" x="34" y="58" width="4" height="2" />
          <rect class="sunmao-tenon" x="34" y="68" width="4" height="2" />
        </svg>
      </div>
      <div class="sunmao-ornament sunmao-br">
        <svg viewBox="0 0 100 100" class="sunmao-svg" preserveAspectRatio="xMidYMid meet">
          <!-- 横向木杆 -->
          <rect class="sunmao-beam-h" x="44" y="60" width="56" height="8" />
          <!-- 纵向木杆 -->
          <rect class="sunmao-beam-v" x="60" y="44" width="8" height="56" />
          <!-- 中心咬合区 -->
          <rect class="sunmao-joint" x="60" y="60" width="8" height="8" />
          <!-- 榫头凸起 -->
          <rect class="sunmao-tenon" x="58" y="62" width="2" height="4" />
          <rect class="sunmao-tenon" x="68" y="62" width="2" height="4" />
          <rect class="sunmao-tenon" x="62" y="58" width="4" height="2" />
          <rect class="sunmao-tenon" x="62" y="68" width="4" height="2" />
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

/* 四角榫卯装饰 - 十字交叉直榫结构 */
.sunmao-ornament {
  position: absolute;
  width: 64px;
  height: 64px;
  opacity: 0;
}

.sunmao-ornament.sunmao-tl {
  top: 8px;
  left: 8px;
}

.sunmao-ornament.sunmao-tr {
  top: 8px;
  right: 8px;
}

.sunmao-ornament.sunmao-bl {
  bottom: 8px;
  left: 8px;
}

.sunmao-ornament.sunmao-br {
  bottom: 8px;
  right: 8px;
}

.home-view.animate-in .sunmao-ornament.sunmao-tl {
  animation: ornamentIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.1s;
}

.home-view.animate-in .sunmao-ornament.sunmao-tr {
  animation: ornamentIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.2s;
}

.home-view.animate-in .sunmao-ornament.sunmao-bl {
  animation: ornamentIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.3s;
}

.home-view.animate-in .sunmao-ornament.sunmao-br {
  animation: ornamentIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.4s;
}

@keyframes ornamentIn {
  0% { opacity: 0; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1); }
}

.sunmao-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* 横向木杆 */
.sunmao-beam-h {
  fill: rgba(139, 38, 53, 0.08);
  stroke: var(--color-seal);
  stroke-width: 1;
  opacity: 0;
}

.home-view.animate-in .sunmao-tl .sunmao-beam-h,
.home-view.animate-in .sunmao-bl .sunmao-beam-h {
  animation: beamSlideFromLeft 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.3s;
}

.home-view.animate-in .sunmao-tr .sunmao-beam-h,
.home-view.animate-in .sunmao-br .sunmao-beam-h {
  animation: beamSlideFromRight 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.45s;
}

/* 纵向木杆 */
.sunmao-beam-v {
  fill: rgba(139, 38, 53, 0.06);
  stroke: var(--color-seal);
  stroke-width: 1;
  opacity: 0;
}

.home-view.animate-in .sunmao-tl .sunmao-beam-v,
.home-view.animate-in .sunmao-tr .sunmao-beam-v {
  animation: beamSlideFromTop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.5s;
}

.home-view.animate-in .sunmao-bl .sunmao-beam-v,
.home-view.animate-in .sunmao-br .sunmao-beam-v {
  animation: beamSlideFromBottom 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.65s;
}

/* 中心咬合区 */
.sunmao-joint {
  fill: var(--color-seal);
  opacity: 0;
}

.home-view.animate-in .sunmao-joint {
  animation: jointLock 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 0.8s;
}

/* 榫头凸起 */
.sunmao-tenon {
  fill: var(--color-accent);
  opacity: 0;
}

.home-view.animate-in .sunmao-tenon {
  animation: tenonPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: 1s;
}

/* 动画关键帧 */
@keyframes beamSlideFromLeft {
  0% { opacity: 0; transform: translateX(-40px); }
  100% { opacity: 1; transform: translateX(0); }
}

@keyframes beamSlideFromRight {
  0% { opacity: 0; transform: translateX(40px); }
  100% { opacity: 1; transform: translateX(0); }
}

@keyframes beamSlideFromTop {
  0% { opacity: 0; transform: translateY(-40px); }
  100% { opacity: 1; transform: translateY(0); }
}

@keyframes beamSlideFromBottom {
  0% { opacity: 0; transform: translateY(40px); }
  100% { opacity: 1; transform: translateY(0); }
}

@keyframes jointLock {
  0% { opacity: 0; transform: scale(0); }
  50% { opacity: 1; transform: scale(1.2); }
  100% { opacity: 1; transform: scale(1); }
}

@keyframes tenonPop {
  0% { opacity: 0; transform: scale(0); }
  100% { opacity: 1; transform: scale(1); }
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
    padding: 48px 20px 32px;
  }

  /* Mobile 四角装饰缩小 */
  .sunmao-ornament {
    width: 36px;
    height: 36px;
  }

  .sunmao-ornament.sunmao-tl {
    top: 2px;
    left: 2px;
  }

  .sunmao-ornament.sunmao-tr {
    top: 2px;
    right: 2px;
  }

  .sunmao-ornament.sunmao-bl {
    bottom: 2px;
    left: 2px;
  }

  .sunmao-ornament.sunmao-br {
    bottom: 2px;
    right: 2px;
  }

  /* Mobile 木杆变细 */
  .sunmao-beam-h,
  .sunmao-beam-v {
    stroke-width: 0.8;
  }

  .sunmao-joint {
    stroke-width: 0.5;
  }

  .sunmao-tenon {
    stroke-width: 0.5;
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
