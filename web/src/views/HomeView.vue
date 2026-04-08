<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  BookOutline, 
  PeopleOutline, 
  TextOutline,
  ArrowForwardOutline
} from '@vicons/ionicons5'

import { usePoems } from '@/composables/usePoems'
import { useAuthors } from '@/composables/useAuthors'
import { useWordcount } from '@/composables/useWordcount'
import { useLoading } from '@/composables/useLoading'

import { AnimatedStatCard } from '@/components/ui/animated'
import RandomPoemCard from '@/components/content/RandomPoemCard.vue'

const router = useRouter()
const loading = useLoading()

const poems = usePoems()
const authors = useAuthors()
const wordcount = useWordcount()

const animationStarted = ref(false)

const loadingCopy = {
  initializing: '正在启动...',
  loading: '正在加载元数据...',
  complete: '加载完成',
  error: '加载失败，请刷新重试',
}

const statCard1 = ref<InstanceType<typeof AnimatedStatCard> | null>(null)
const statCard2 = ref<InstanceType<typeof AnimatedStatCard> | null>(null)
const statCard3 = ref<InstanceType<typeof AnimatedStatCard> | null>(null)

const loadAllData = async () => {
  animationStarted.value = false
  loading.startBlocking(loadingCopy.initializing, loadingCopy.loading)

  try {
    loading.updatePhase('metadata', loadingCopy.loading)
    loading.updateProgress(0, 3)
    await poems.loadMetadata(true)

    loading.updateProgress(1, 3, loadingCopy.loading)
    await authors.loadMetadata(true)

    loading.updateProgress(2, 3, loadingCopy.loading)
    await wordcount.loadMetadata(true)

    loading.updatePhase('complete', loadingCopy.complete)
    loading.updateProgress(3, 3)

    setTimeout(() => {
      loading.finish()
      setTimeout(() => {
        animationStarted.value = true
      }, 100)
    }, 500)
  } catch (error) {
    loading.error(loadingCopy.error)
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

const features = [
  {
    icon: BookOutline,
    title: '诗词检索',
    desc: '三十万首诗词，按朝代、体裁、作者智能检索',
    path: '/poems',
    color: 'teal'
  },
  {
    icon: PeopleOutline,
    title: '作者分析',
    desc: '诗人群体画像，作品风格与成就分析',
    path: '/authors',
    color: 'amber'
  },
  {
    icon: TextOutline,
    title: '分词数据',
    desc: '高频字词分析，洞悉诗词用字规律',
    path: '/word-count',
    color: 'plum'
  }
]

const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<template>
  <div class="home-view" :class="{ 'animate-in': animationStarted }">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-bg">
        <div class="bg-gradient"></div>
        <div class="bg-pattern"></div>
      </div>
      
      <div class="hero-content">
        <h1 class="hero-title">
          中华古典诗词数据挖掘平台
        </h1>
        
        <p class="hero-desc">
          基于 chinese-poetry 开源数据库构建<br/>
          收录全唐诗、全宋诗、全宋词三大诗词库
        </p>

        <div class="hero-stats">
          <div class="hero-stat">
            <span class="stat-num">33.3万</span>
            <span class="stat-label">首诗词</span>
          </div>
          <div class="hero-stat">
            <span class="stat-num">1.3万</span>
            <span class="stat-label">位诗人</span>
          </div>
          <div class="hero-stat">
            <span class="stat-num">89.4万</span>
            <span class="stat-label">个词汇</span>
          </div>
        </div>
        
        <div class="hero-actions">
          <button class="btn btn-primary" @click="navigateTo('/poems')">
            <span>开始探索</span>
            <ArrowForwardOutline />
          </button>
        </div>
      </div>
    </section>

    <!-- Random Poem Section -->
    <section class="random-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">
            <SparklesOutline class="title-icon" />
            今日诗推荐
          </h2>
          <p class="section-desc">随机抽取一首，感受诗词之美</p>
        </div>
        <RandomPoemCard />
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">功能概览</h2>
          <p class="section-desc">多种方式探索诗词世界</p>
        </div>
        
        <div class="features-grid">
          <article 
            v-for="(feature, index) in features" 
            :key="feature.title"
            class="feature-card"
            :style="{ '--delay': `${index * 0.1}s` }"
            @click="navigateTo(feature.path)"
          >
            <div class="feature-icon" :class="feature.color">
              <component :is="feature.icon" />
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.desc }}</p>
            <div class="feature-arrow">
              <ArrowForwardOutline />
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-view {
  min-height: 100vh;
  background: var(--bg-primary);
}

.container {
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: 0 var(--space-4);
}

@media (min-width: 768px) {
  .container {
    padding: 0 var(--space-6);
  }
}

/* ═══════════════════════════════════════════════════════════════
   Hero Section - 水墨意境
══════════════════════════════════════════════════════════════ */
.hero-section {
  position: relative;
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-4);
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(ellipse 80% 60% at 50% 120%, rgba(45, 106, 106, 0.08) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 20% 0%, rgba(45, 106, 106, 0.05) 0%, transparent 50%),
    radial-gradient(ellipse 50% 30% at 80% 100%, rgba(107, 58, 91, 0.04) 0%, transparent 50%);
}

.bg-pattern {
  position: absolute;
  inset: 0;
  opacity: 0.4;
  background-image: 
    radial-gradient(circle at 25% 25%, var(--ink-fog) 1px, transparent 1px),
    radial-gradient(circle at 75% 75%, var(--ink-fog) 1px, transparent 1px);
  background-size: 60px 60px;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 720px;
  animation: fadeInUp 0.8s var(--ease-out-expo) forwards;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--ink-fog);
  border: var(--border-light);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--ink-gray);
  margin-bottom: var(--space-6);
}

.badge-icon {
  width: 16px;
  height: 16px;
  color: var(--accent-teal);
}

.hero-title {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: 0 0 var(--space-6);
}

.title-line {
  font-family: var(--font-serif);
  font-size: var(--text-4xl);
  font-weight: 700;
  color: var(--ink-dark);
  letter-spacing: 0.1em;
  line-height: 1.2;
}

.title-line.accent {
  color: var(--accent-teal);
}

.hero-desc {
  font-size: var(--text-lg);
  color: var(--ink-gray);
  line-height: 1.8;
  margin: 0 0 var(--space-8);
}

.hero-actions {
  display: flex;
  justify-content: center;
  margin-top: var(--space-6);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  font-size: var(--text-base);
  font-weight: 500;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s var(--ease-out-quart);
}

.btn-primary {
  background: var(--ink-dark);
  color: var(--paper-white);
  border: none;
}

.btn-primary:hover {
  background: var(--ink-medium);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: var(--space-8);
  margin-top: var(--space-6);
}

.hero-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--accent-teal);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--ink-gray);
}

/* ═══════════════════════════════════════════════════════════════
   Stats Section
══════════════════════════════════════════════════════════════ */
.stats-section {
  padding: var(--space-12) 0;
  background: var(--bg-secondary);
  border-top: var(--border-light);
  border-bottom: var(--border-light);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
}

/* ═══════════════════════════════════════════════════════════════
   Random Poem Section
══════════════════════════════════════════════════════════════ */
.random-section {
  padding: var(--space-16) 0;
}

.section-header {
  text-align: center;
  margin-bottom: var(--space-10);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--ink-dark);
  margin: 0 0 var(--space-2);
}

.title-icon {
  width: 24px;
  height: 24px;
  color: var(--accent-teal);
}

.section-desc {
  font-size: var(--text-base);
  color: var(--ink-gray);
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════════
   Features Section
══════════════════════════════════════════════════════════════ */
.features-section {
  padding: var(--space-16) 0;
  background: var(--bg-secondary);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
}

@media (max-width: 1024px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
}

.feature-card {
  position: relative;
  padding: var(--space-8);
  background: var(--bg-card);
  border: var(--border-light);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all 0.4s var(--ease-out-expo);
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--ink-fog);
  transition: background 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--ink-mist);
}

.feature-card:hover::before {
  background: var(--accent-teal);
}

.feature-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-5);
  transition: transform 0.3s var(--ease-out-quart);
}

.feature-icon svg {
  width: 28px;
  height: 28px;
}

.feature-icon.teal {
  background: rgba(45, 106, 106, 0.1);
  color: var(--accent-teal);
}

.feature-icon.amber {
  background: rgba(184, 134, 11, 0.1);
  color: var(--accent-amber);
}

.feature-icon.plum {
  background: rgba(107, 58, 91, 0.1);
  color: var(--accent-plum);
}

.feature-card:hover .feature-icon {
  transform: scale(1.1);
}

.feature-title {
  font-family: var(--font-serif);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--ink-dark);
  margin: 0 0 var(--space-2);
}

.feature-desc {
  font-size: var(--text-sm);
  color: var(--ink-gray);
  line-height: 1.6;
  margin: 0;
}

.feature-arrow {
  position: absolute;
  bottom: var(--space-6);
  right: var(--space-6);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ink-fog);
  border-radius: var(--radius-full);
  color: var(--ink-light);
  opacity: 0;
  transform: translateX(-8px);
  transition: all 0.3s var(--ease-out-quart);
}

.feature-arrow svg {
  width: 16px;
  height: 16px;
}

.feature-card:hover .feature-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* ═══════════════════════════════════════════════════════════════
   Intro Section
══════════════════════════════════════════════════════════════ */
.intro-section {
  padding: var(--space-16) 0;
}

.intro-card {
  background: var(--bg-card);
  border: var(--border-light);
  border-radius: var(--radius-xl);
  padding: var(--space-10);
  text-align: center;
}

.intro-title {
  font-family: var(--font-serif);
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--ink-dark);
  margin: 0 0 var(--space-6);
}

.intro-text {
  font-size: var(--text-base);
  color: var(--ink-gray);
  line-height: 1.8;
  max-width: 640px;
  margin: 0 auto var(--space-8);
}

.intro-link {
  color: var(--accent-teal);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.intro-link:hover {
  color: var(--accent-jade);
}

.intro-stats {
  display: flex;
  justify-content: center;
  gap: var(--space-10);
  padding-top: var(--space-6);
  border-top: var(--border-light);
}

.intro-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-family: var(--font-serif);
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--accent-teal);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--ink-gray);
  margin-top: var(--space-1);
}

/* ═══════════════════════════════════════════════════════════════
   Responsive
══════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .hero-section {
    min-height: 60vh;
    padding: var(--space-12) var(--space-4);
  }
  
  .title-line {
    font-size: var(--text-3xl);
    letter-spacing: 0.05em;
  }
  
  .hero-desc {
    font-size: var(--text-base);
  }
  
  .btn {
    padding: var(--space-3) var(--space-5);
    font-size: var(--text-sm);
  }
  
  .intro-stats {
    flex-direction: column;
    gap: var(--space-6);
  }
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
