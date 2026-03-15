<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchIndex } from '@/composables/useSearchIndex'
import { NCard, NTag, NSpin, NEmpty, NButton, NInput, NIcon, NAvatar, NDivider } from 'naive-ui'
import { SearchOutline, SparklesOutline, LeafOutline, ArrowForwardOutline, BookOutline, TimeOutline } from '@vicons/ionicons5'

const router = useRouter()
const { getRandomKeywordIndex, searchByKeyword, loading, initialized } = useSearchIndex()

const searchQuery = ref('')
const currentKeyword = ref('')
const results = ref<Array<{
  id: string
  title: string
  author: string
  dynasty: string
  score: number
}>>([])
const hasSearched = ref(false)
const searchTime = ref(0)
const searchSuggestions = ref<string[]>(['春风', '明月', '青山', '绿水', '相思', '离别的', '秋夜', '江上'])

const handleRandomSearch = async () => {
  hasSearched.value = true
  const startTime = performance.now()
  const data = await getRandomKeywordIndex()
  searchTime.value = Math.round(performance.now() - startTime)
  currentKeyword.value = data.keyword
  results.value = data.poems
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  hasSearched.value = true
  currentKeyword.value = searchQuery.value
  
  const startTime = performance.now()
  results.value = await searchByKeyword(searchQuery.value)
  searchTime.value = Math.round(performance.now() - startTime)
}

const handleSuggestionClick = (keyword: string) => {
  searchQuery.value = keyword
  handleSearch()
}

const goToPoem = (id: string) => {
  router.push(`/poems/${id}`)
}

const dynastyConfig: Record<string, { color: string; bg: string; label: string }> = {
  '唐': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', label: '盛唐' },
  '宋': { color: '#1E40AF', bg: 'rgba(30, 64, 175, 0.08)', label: '两宋' },
  '元': { color: '#047857', bg: 'rgba(4, 120, 87, 0.08)', label: '元代' },
  '明': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', label: '明代' },
  '清': { color: '#7C3AED', bg: 'rgba(124, 58, 237, 0.08)', label: '清代' },
  '近现代': { color: '#DC2626', bg: 'rgba(220, 38, 38, 0.08)', label: '近现代' }
}

const getDynastyConfig = (dynasty: string) => {
  return dynastyConfig[dynasty] || { color: '#5C5244', bg: 'rgba(92, 82, 68, 0.08)', label: dynasty }
}

const currentTime = ref(new Date().getHours())
const greeting = computed(() => {
  if (currentTime.value < 6) return '夜深了'
  if (currentTime.value < 12) return '晨安'
  if (currentTime.value < 14) return '午安'
  if (currentTime.value < 18) return '下午好'
  return '晚安'
})

onMounted(() => {
  handleRandomSearch()
})
</script>

<template>
  <div class="home-view">
    <section class="hero-section">
      <div class="hero-decoration top-left"></div>
      <div class="hero-decoration bottom-right"></div>
      
      <div class="hero-content">
        <div class="greeting">
          <span class="greeting-icon">◐</span>
          {{ greeting }}，寻诗者
        </div>
        
        <h1 class="hero-title">
          <span class="title-main">墨韵诗海</span>
          <span class="title-sub">三十万首诗词的智慧之库</span>
        </h1>
        
        <p class="hero-description">
          穿越唐宋元明清的诗酒风流，<br/>
          以关键词为舟，泛舟词海，寻觅千古名句
        </p>

        <div class="search-container">
          <div class="search-box">
            <NInput
              v-model:value="searchQuery"
              placeholder="输入意象、情感或关键词..."
              size="large"
              class="search-input"
              @keyup.enter="handleSearch"
              :loading="loading"
            >
              <template #prefix>
                <NIcon :component="SearchOutline" class="search-icon" />
              </template>
            </NInput>
            <NButton 
              type="primary" 
              size="large" 
              @click="handleSearch" 
              :loading="loading"
              class="search-btn"
            >
              寻诗
            </NButton>
          </div>
          
          <div class="search-tips" v-if="!hasSearched">
            <span class="tips-label">试试：</span>
            <button 
              v-for="kw in searchSuggestions" 
              :key="kw" 
              class="suggestion-chip"
              @click="handleSuggestionClick(kw)"
            >
              {{ kw }}
            </button>
          </div>
        </div>

        <div class="hero-stats" v-if="initialized">
          <div class="stat-item">
            <span class="stat-number">332,712</span>
            <span class="stat-label">首诗词</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">11.5万</span>
            <span class="stat-label">个关键词</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">200+</span>
            <span class="stat-label">个索引分片</span>
          </div>
        </div>
      </div>
    </section>

    <section class="results-section" v-if="hasSearched">
      <div class="results-header">
        <div class="results-meta">
          <h2 class="results-title">
            <NIcon :component="BookOutline" class="title-icon" />
            搜索结果
          </h2>
          <div class="results-info">
            <NTag type="primary" size="small" round>
              关键词：{{ currentKeyword }}
            </NTag>
            <span class="result-count">{{ results.length }} 首</span>
            <span class="search-time" v-if="searchTime > 0">
              <NIcon :component="TimeOutline" />
              {{ searchTime }}ms
            </span>
          </div>
        </div>
        
        <NButton 
          quaternary 
          size="small" 
          @click="handleRandomSearch" 
          :loading="loading"
          class="refresh-btn"
        >
          <template #icon>
            <SparklesOutline />
          </template>
          换一批
        </NButton>
      </div>

      <NSpin :show="loading && !initialized">
        <NEmpty v-if="results.length === 0 && !loading" description="未在词海中发现此意象，试试其他关键词">
          <template #extra>
            <NButton @click="handleRandomSearch">随机探索</NButton>
          </template>
        </NEmpty>
        
        <div v-else class="poems-grid">
          <article 
            v-for="(poem, index) in results" 
            :key="poem.id"
            class="poem-card"
            :style="{ '--delay': `${index * 50}ms` }"
            @click="goToPoem(poem.id)"
          >
            <div class="poem-card-inner">
              <div class="poem-header">
                <h3 class="poem-title">{{ poem.title }}</h3>
                <span 
                  class="dynasty-badge"
                  :style="{ 
                    color: getDynastyConfig(poem.dynasty).color,
                    background: getDynastyConfig(poem.dynasty).bg 
                  }"
                >
                  {{ poem.dynasty }}
                </span>
              </div>
              
              <div class="poem-author">
                <NAvatar 
                  :size="24" 
                  round
                  :style="{ backgroundColor: getDynastyConfig(poem.dynasty).bg }"
                >
                  {{ poem.author.charAt(0) }}
                </NAvatar>
                <span class="author-name">{{ poem.author }}</span>
              </div>
              
              <div class="poem-footer">
                <span class="read-more">
                  品读全文
                  <NIcon :component="ArrowForwardOutline" />
                </span>
              </div>
            </div>
          </article>
        </div>
      </NSpin>
    </section>

    <section class="intro-section" v-if="!hasSearched">
      <div class="intro-card">
        <div class="intro-icon">
          <NIcon :component="LeafOutline" :size="32" />
        </div>
        <h3>如何使用</h3>
        <ul class="intro-list">
          <li><span class="num">壹</span>输入任意关键词：春风、明月、青楼、离愁...</li>
          <li><span class="num">贰</span>系统将检索三十万首诗词</li>
          <li><span class="num">叁</span>点击任意结果查看诗全文与格律分析</li>
        </ul>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1000px;
  margin: 0 auto;
}

.hero-section {
  position: relative;
  padding: 48px 40px;
  background: var(--color-bg-paper);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  overflow: hidden;
  margin-bottom: 32px;
}

.hero-decoration {
  position: absolute;
  width: 200px;
  height: 200px;
  pointer-events: none;
}

.hero-decoration.top-left {
  top: -60px;
  left: -60px;
  background: radial-gradient(circle, rgba(139, 38, 53, 0.06) 0%, transparent 70%);
}

.hero-decoration.bottom-right {
  bottom: -80px;
  right: -80px;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(201, 169, 110, 0.08) 0%, transparent 70%);
}

.hero-content {
  position: relative;
  z-index: 1;
}

.greeting {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-ink-light);
  margin-bottom: 16px;
  letter-spacing: 2px;
}

.greeting-icon {
  font-size: 18px;
  color: var(--color-seal);
}

.hero-title {
  margin: 0 0 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-main {
  font-family: "Noto Serif SC", serif;
  font-size: 42px;
  font-weight: 700;
  color: var(--color-ink);
  letter-spacing: 8px;
  background: linear-gradient(135deg, var(--color-ink) 0%, var(--color-seal) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-sub {
  font-size: 14px;
  color: var(--color-ink-light);
  letter-spacing: 4px;
}

.hero-description {
  margin: 0 0 32px;
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-ink-light);
}

.search-container {
  max-width: 580px;
}

.search-box {
  display: flex;
  gap: 8px;
}

.search-input {
  flex: 1;
}

.search-input :deep(.n-input__input-el) {
  font-size: 16px;
}

.search-icon {
  color: var(--color-ink-light);
}

.search-btn {
  min-width: 80px;
  font-weight: 500;
  letter-spacing: 2px;
}

.search-tips {
  margin-top: 16px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.tips-label {
  font-size: 13px;
  color: var(--color-ink-light);
}

.suggestion-chip {
  padding: 4px 12px;
  background: rgba(139, 38, 53, 0.04);
  border: 1px solid rgba(139, 38, 53, 0.12);
  border-radius: 16px;
  font-size: 13px;
  color: var(--color-seal);
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestion-chip:hover {
  background: rgba(139, 38, 53, 0.1);
  border-color: var(--color-seal);
  transform: translateY(-1px);
}

.hero-stats {
  margin-top: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-number {
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-seal);
}

.stat-label {
  font-size: 12px;
  color: var(--color-ink-light);
  letter-spacing: 1px;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--color-border);
}

.results-section {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.results-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.results-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.results-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ink);
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  color: var(--color-seal);
}

.results-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--color-ink-light);
}

.result-count {
  font-weight: 500;
}

.search-time {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(139, 38, 53, 0.04);
  border-radius: 4px;
  font-size: 12px;
}

.refresh-btn {
  color: var(--color-ink-light);
}

.poems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.poem-card {
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: slideUp 0.4s ease backwards;
  animation-delay: var(--delay);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.poem-card:hover {
  border-color: var(--color-seal);
  box-shadow: var(--shadow-card);
  transform: translateY(-4px);
}

.poem-card-inner {
  padding: 20px;
}

.poem-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.poem-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--color-ink);
  line-height: 1.4;
}

.dynasty-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
  letter-spacing: 1px;
}

.poem-author {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.author-name {
  font-size: 14px;
  color: var(--color-ink-light);
}

.poem-footer {
  display: flex;
  justify-content: flex-end;
}

.read-more {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-seal);
  opacity: 0;
  transform: translateX(-8px);
  transition: all 0.2s ease;
}

.poem-card:hover .read-more {
  opacity: 1;
  transform: translateX(0);
}

.intro-section {
  margin-top: 32px;
}

.intro-card {
  padding: 32px;
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  text-align: center;
}

.intro-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 38, 53, 0.06);
  border-radius: 50%;
  color: var(--color-seal);
}

.intro-card h3 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
}

.intro-list {
  margin: 0;
  padding: 0;
  list-style: none;
  text-align: left;
  max-width: 400px;
  margin: 0 auto;
}

.intro-list li {
  padding: 8px 0;
  font-size: 14px;
  color: var(--color-ink-light);
  display: flex;
  align-items: center;
  gap: 12px;
}

.intro-list .num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--color-seal);
  color: #fff;
  font-size: 12px;
  border-radius: 4px;
  flex-shrink: 0;
}
</style>
