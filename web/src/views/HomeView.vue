<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { BookOutline, PeopleOutline, GitNetworkOutline } from '@vicons/ionicons5'

import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { useLoading } from '@/composables/useLoading'

import { SunmaoOrnament, BreathingFrame } from '@/components/ui/decorative'
import { AnimatedStatCard } from '@/components/ui/animated'
import RandomPoemCard from '@/components/content/RandomPoemCard.vue'

const router = useRouter()
const loading = useLoading()

const poemsV2 = usePoemsV2()
const authorsV2 = useAuthorsV2()
const wordSimilarityV2 = useWordSimilarityV2()

const animationStarted = ref(false)

const loadingCopy = {
  initializing: [
    '文脉初启，正在唤醒千年诗魂...',
    '墨香渐起，诗卷缓缓展开...',
    '寻诗之旅，即将启程...',
    '千年文脉，待君品鉴...'
  ],
  loading: [
    '正在翻阅诗词典藏目录...',
    '正在整理诗人名录档案...',
    '正在汇聚词频统计数据...',
    '正在梳理朝代更迭脉络...',
    '正在采撷千古名句精华...'
  ],
  complete: [
    '文脉已通，请君品鉴',
    '诗卷已展，静候知音',
    '千年诗魂，已然苏醒',
    '万首诗词，待君采撷'
  ],
  error: [
    '文脉暂断，请刷新重试',
    '诗卷难展，稍后再试',
    '墨香暂散，请重新启程'
  ]
}

const getRandomCopy = (copyArray: string[]): string => {
  const index = Math.floor(Math.random() * copyArray.length)
  return copyArray[index] ?? ''
}

const pageTitleCopy = {
  home: {
    title: '文脉千秋',
    subtitle: '数字诗学图谱'
  }
}

const poeticQuotes = [
  '腹有诗书气自华',
  '读书破万卷，下笔如有神',
  '文章千古事，得失寸心知',
  '李杜文章在，光焰万丈长',
  '采菊东篱下，悠然见南山',
  '会当凌绝顶，一览众山小',
  '山重水复疑无路，柳暗花明又一村',
  '问君能有几多愁，恰似一江春水向东流'
]

// 添加调试日志和组件引用
const statCard1 = ref<InstanceType<typeof AnimatedStatCard> | null>(null)
const statCard2 = ref<InstanceType<typeof AnimatedStatCard> | null>(null)
const statCard3 = ref<InstanceType<typeof AnimatedStatCard> | null>(null)

const loadAllData = async () => {
  animationStarted.value = false

  loading.startBlocking(
    getRandomCopy(loadingCopy.initializing),
    getRandomCopy(loadingCopy.loading)
  )

  try {
    loading.updatePhase('metadata', getRandomCopy(loadingCopy.loading))
    loading.updateProgress(0, 3)
    await poemsV2.loadMetadata()

    loading.updateProgress(1, 3, getRandomCopy(loadingCopy.loading))
    await authorsV2.loadMetadata()

    loading.updateProgress(2, 3, getRandomCopy(loadingCopy.loading))
    await wordSimilarityV2.loadMetadata()

    loading.updatePhase('complete', getRandomCopy(loadingCopy.complete))
    loading.updateProgress(3, 3)

    setTimeout(() => {
      loading.finish()
      setTimeout(() => {
        animationStarted.value = true
      }, 100)
    }, 500)
  } catch (error) {
    loading.error(getRandomCopy(loadingCopy.error))
    console.error('数据加载失败:', error)
  }
}

onMounted(() => {
  // 调试日志：检查布局尺寸
  console.log('[HomeView] onMounted - checking layout dimensions')
  const heroSection = document.querySelector('.hero-section')
  const homeView = document.querySelector('.home-view')
  const mainContent = document.querySelector('.main-content')
  if (heroSection) {
    const rect = heroSection.getBoundingClientRect()
    console.log('[HomeView] hero-section dimensions:', { width: rect.width, height: rect.height })
  }
  if (homeView) {
    const rect = homeView.getBoundingClientRect()
    console.log('[HomeView] home-view dimensions:', { width: rect.width, height: rect.height })
  }
  if (mainContent) {
    const rect = mainContent.getBoundingClientRect()
    console.log('[HomeView] main-content dimensions:', { width: rect.width, height: rect.height })
  }

  loadAllData()
})

const formatNumber = (num: number | undefined | null): string => {
  if (num === undefined || num === null) return '--'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

const animatedNumbers = ref({
  authors: 0,
  poems: 0,
  vocab: 0
})

watch(() => animationStarted.value, (started) => {
  console.log('[HomeView] animationStarted changed:', started)
  if (started) {
    console.log('[HomeView] Triggering stat card animations...')
    console.log('[HomeView] statCard1 ref:', statCard1.value)
    console.log('[HomeView] statCard2 ref:', statCard2.value)
    console.log('[HomeView] statCard3 ref:', statCard3.value)

    // 触发每个卡片的动画
    statCard1.value?.startAnimation()
    statCard2.value?.startAnimation()
    statCard3.value?.startAnimation()

    setTimeout(() => animatedNumbers.value.authors = authorsV2.totalAuthors.value || 0, 800)
    setTimeout(() => animatedNumbers.value.poems = poemsV2.totalPoems.value || 0, 1000)
    setTimeout(() => animatedNumbers.value.vocab = wordSimilarityV2.vocabSize.value || 0, 1200)
  }
})
</script>

<template>
  <div class="home-view" :class="{ 'animate-in': animationStarted }">
    <section class="hero-section">
      <div class="hero-bg">
        <div class="bg-gradient"></div>
        <div class="bg-texture"></div>
      </div>



      <div class="hero-content">
        <div class="time-greeting">
          <span class="greeting-text">寻诗者</span>
          <span class="greeting-divider"></span>
          <span class="greeting-sub">今日可有所得</span>
        </div>

        <div class="title-block">
          <span
            class="title-zh"
            v-for="(char, i) in pageTitleCopy.home.title.split('')"
            :key="i"
            :style="{ animationDelay: `${0.3 + i * 0.12}s` }"
          >
            {{ char }}
          </span>
        </div>

        <h1 class="hero-title">
          <span class="title-main">{{ pageTitleCopy.home.subtitle }}</span>
        </h1>

        <p class="hero-subtitle">
          <span class="subtitle-line">{{ pageTitleCopy.home.subtitle }}</span>
        </p>
      </div>
    </section>

    <section class="stats-section">
      <div class="stats-grid">
        <AnimatedStatCard
          ref="statCard1"
          label="位诗人"
          :value="animatedNumbers.authors"
          :prefix-icon="PeopleOutline"
          :animation-delay="800"
          :animation-duration="1500"
          :formatter="formatNumber"
        />
        <AnimatedStatCard
          ref="statCard2"
          label="首诗词"
          :value="animatedNumbers.poems"
          :prefix-icon="BookOutline"
          :animation-delay="1000"
          :animation-duration="1800"
          :formatter="formatNumber"
        />
        <AnimatedStatCard
          ref="statCard3"
          label="个词条"
          :value="animatedNumbers.vocab"
          :prefix-icon="GitNetworkOutline"
          :animation-delay="1200"
          :animation-duration="1200"
          :formatter="formatNumber"
        />
      </div>
    </section>

    <section class="random-poem-section" :style="{ animationDelay: '1.1s' }">
      <RandomPoemCard />
    </section>

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
  padding: 16px 32px 32px;
  /* 修复：使用更精确的高度计算，避免页面超出 */
  min-height: calc(100vh - 64px - 80px);
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 16px;
}

.hero-section {
  position: relative;
  padding: 32px 40px 28px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  /* 修复：改为 visible，让 SunmaoOrnament 可以显示在边缘 */
  overflow: visible;
}

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

.hero-content {
  position: relative;
  z-index: 10;
  text-align: center;
}

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

.stats-section {
  padding: 0;
  opacity: 0;
  transform: translateY(20px);
}

.animate-in .stats-section {
  animation: fadeInUp 0.6s ease forwards;
  animation-delay: 0.6s;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.random-poem-section {
  padding: 0;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  opacity: 0;
  transform: translateY(20px);
}

.animate-in .random-poem-section {
  animation: fadeInUp 0.6s ease forwards;
}

.intro-section {
  padding: 0;
}

.intro-frame {
  position: relative;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  padding: 28px 32px;
  opacity: 0;
  transform: translateY(20px);
}

.animate-in .intro-frame {
  animation: fadeInUp 0.6s ease forwards;
}

.frame-corner {
  position: absolute;
  width: 12px;
  height: 12px;
  border-color: var(--color-seal);
  border-style: solid;
  opacity: 0.3;
}

.frame-corner.tl {
  top: 8px;
  left: 8px;
  border-width: 1px 0 0 1px;
}

.frame-corner.tr {
  top: 8px;
  right: 8px;
  border-width: 1px 1px 0 0;
}

.frame-corner.bl {
  bottom: 8px;
  left: 8px;
  border-width: 0 0 1px 1px;
}

.frame-corner.br {
  bottom: 8px;
  right: 8px;
  border-width: 0 1px 1px 0;
}

.intro-content {
  text-align: center;
}

.intro-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-ink-light);
  margin: 0;
}

.intro-link {
  color: var(--color-seal);
  text-decoration: none;
  font-weight: 500;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
}

.intro-link:hover {
  border-bottom-color: var(--color-seal);
}

@media (max-width: 768px) {
  .home-view {
    padding: 16px;
    gap: 16px;
  }

  .hero-section {
    padding: 32px 20px;
  }

  .title-zh {
    font-size: 32px;
  }

  .title-main {
    font-size: 20px;
    letter-spacing: 8px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .intro-frame {
    padding: 20px;
  }
}
</style>
