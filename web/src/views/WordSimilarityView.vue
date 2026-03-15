<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWordSimilarity } from '@/composables/useWordSimilarity'
import { useSearchIndex } from '@/composables/useSearchIndex'
import {
  NCard,
  NInput,
  NButton,
  NSlider,
  NTag,
  NSpin,
  NEmpty,
  NTabs,
  NTabPane,
  NList,
  NListItem,
  NThing,
  NProgress,
  NBadge,
  NSpace,
  NDivider,
  NTooltip,
  NIcon,
  NGrid,
  NGridItem,
  NStatistic,
  NAlert
} from 'naive-ui'
import {
  SearchOutline,
  GitNetworkOutline,
  ListOutline,
  BookOutline,
  SparklesOutline,
  TrendingUpOutline,
  LayersOutline,
  ArrowForwardOutline,
  RefreshOutline
} from '@vicons/ionicons5'
import WordNetworkGraph from '@/components/WordNetworkGraph.vue'

const router = useRouter()
const { isReady, isLoading, error, vocabSize, getSimilarWords, hasWord } = useWordSimilarity()
const { searchByKeyword } = useSearchIndex()

// 搜索状态
const searchWord = ref('')
const searchedWord = ref('')
const minSimilarity = ref(0.7)
const searching = ref(false)
const similarWords = ref<{ word: string; similarity: number }[]>([])

// 相关诗词
const relatedPoems = ref<Array<{
  id: string
  title: string
  author: string
  dynasty: string
  score: number
}>>([])
const loadingPoems = ref(false)

// 历史记录
const searchHistory = ref<string[]>([])

// 热门词推荐
const hotWords = ['春风', '明月', '青山', '相思', '落花', '秋水', '故人', '天涯']

// 计算属性
const hasResults = computed(() => similarWords.value.length > 0)
const highSimilarityWords = computed(() => 
  similarWords.value.filter(w => w.similarity >= 0.85)
)
const mediumSimilarityWords = computed(() => 
  similarWords.value.filter(w => w.similarity >= 0.75 && w.similarity < 0.85)
)
const lowSimilarityWords = computed(() => 
  similarWords.value.filter(w => w.similarity < 0.75)
)

// 加载历史记录
onMounted(() => {
  const saved = localStorage.getItem('wordSimilarityHistory')
  if (saved) {
    searchHistory.value = JSON.parse(saved)
  }
})

// 保存历史记录
function saveHistory(word: string) {
  if (!word || searchHistory.value.includes(word)) return
  searchHistory.value.unshift(word)
  if (searchHistory.value.length > 10) {
    searchHistory.value = searchHistory.value.slice(0, 10)
  }
  localStorage.setItem('wordSimilarityHistory', JSON.stringify(searchHistory.value))
}

// 搜索相似词
async function handleSearch() {
  if (!searchWord.value.trim() || !isReady.value) return
  
  const word = searchWord.value.trim()
  if (!hasWord(word)) {
    similarWords.value = []
    searchedWord.value = word
    return
  }

  searching.value = true
  searchedWord.value = word

  try {
    similarWords.value = await getSimilarWords(word, minSimilarity.value)
    saveHistory(word)
    await loadRelatedPoems(word)
  } catch (err) {
    console.error('Search failed:', err)
    similarWords.value = []
  } finally {
    searching.value = false
  }
}

// 加载相关诗词
async function loadRelatedPoems(word: string) {
  loadingPoems.value = true
  try {
    // 获取 top 3 相似词 + 原词 一起搜索
    const topSimilar = similarWords.value.slice(0, 3).map(w => w.word)
    const searchTerms = [word, ...topSimilar]
    
    // 使用第一个词搜索（简化版）
    const poems = await searchByKeyword(word)
    relatedPoems.value = poems.slice(0, 6)
  } catch (err) {
    console.error('Failed to load related poems:', err)
    relatedPoems.value = []
  } finally {
    loadingPoems.value = false
  }
}

// 快速选择词
function selectWord(word: string) {
  searchWord.value = word
  handleSearch()
}

// 跳转到诗词详情
function goToPoem(id: string) {
  router.push(`/poems/${id}`)
}

// 获取相似度颜色
function getSimilarityColor(similarity: number): string {
  if (similarity >= 0.9) return '#18a058'
  if (similarity >= 0.8) return '#2080f0'
  if (similarity >= 0.75) return '#f0a020'
  return '#d03050'
}

// 获取相似度标签类型
function getSimilarityType(similarity: number): 'success' | 'info' | 'warning' | 'error' {
  if (similarity >= 0.9) return 'success'
  if (similarity >= 0.8) return 'info'
  if (similarity >= 0.75) return 'warning'
  return 'error'
}

// 监听相似度阈值变化
watch(minSimilarity, () => {
  if (searchedWord.value) {
    handleSearch()
  }
})
</script>

<template>
  <div class="word-similarity-view">
    <!-- 头部区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <NIcon :component="GitNetworkOutline" size="48" />
          <span>词境探索</span>
        </h1>
        <p class="hero-subtitle">
          基于 88,000+ 诗词词汇的语义关联网络
          <br />
          <span class="hero-stats">
            已收录 {{ vocabSize.toLocaleString() }} 个词 · 相似度阈值 >0.7
          </span>
        </p>
      </div>
    </section>

    <!-- 搜索区域 -->
    <section class="search-section">
      <NCard class="search-card">
        <!-- 状态提示 -->
        <NAlert v-if="!isReady && !isLoading" type="warning" class="mb-4">
          数据加载失败，请刷新页面重试
        </NAlert>
        
        <div class="search-box">
          <NInput
            v-model:value="searchWord"
            placeholder="输入一词，探索其词境关联，如：春风、明月、相思..."
            size="large"
            :disabled="!isReady"
            @keyup.enter="handleSearch"
            class="search-input"
          >
            <template #prefix>
              <NIcon :component="SearchOutline" />
            </template>
          </NInput>
          <NButton
            type="primary"
            size="large"
            :loading="searching"
            :disabled="!isReady || !searchWord"
            @click="handleSearch"
            class="search-btn"
          >
            探索词境
          </NButton>
        </div>

        <!-- 相似度阈值滑块 -->
        <div class="threshold-control">
          <span class="threshold-label">相似度阈值</span>
          <NSlider
            v-model:value="minSimilarity"
            :min="0.7"
            :max="0.95"
            :step="0.05"
            :marks="{
              0.7: '0.7',
              0.8: '0.8',
              0.9: '0.9',
              0.95: '0.95'
            }"
            style="flex: 1; max-width: 400px;"
          />
          <NTag :type="getSimilarityType(minSimilarity)" size="small">
            {{ minSimilarity.toFixed(2) }}
          </NTag>
        </div>

        <!-- 热门词推荐 -->
        <div class="hot-words">
          <span class="hot-words-label">
            <NIcon :component="SparklesOutline" size="14" />
            热门探索
          </span>
          <NSpace>
            <NTag
              v-for="word in hotWords"
              :key="word"
              class="hot-word-tag"
              @click="selectWord(word)"
            >
              {{ word }}
            </NTag>
          </NSpace>
        </div>

        <!-- 历史记录 -->
        <div v-if="searchHistory.length > 0" class="search-history">
          <span class="history-label">
            <NIcon :component="TrendingUpOutline" size="14" />
            最近探索
          </span>
          <NSpace>
            <NTag
              v-for="word in searchHistory"
              :key="word"
              type="info"
              size="small"
              class="history-tag"
              @click="selectWord(word)"
            >
              {{ word }}
            </NTag>
          </NSpace>
        </div>
      </NCard>
    </section>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <NSpin size="large" />
      <p>正在加载词境数据...</p>
    </div>

    <!-- 搜索结果 -->
    <section v-else-if="searchedWord" class="results-section">
      <!-- 未找到提示 -->
      <NEmpty
        v-if="!hasResults && !searching"
        :description="`「${searchedWord}」暂无相似词数据`"
        class="empty-state"
      >
        <template #extra>
          <p class="empty-hint">尝试降低相似度阈值，或搜索其他词汇</p>
        </template>
      </NEmpty>

      <template v-else-if="hasResults">
        <!-- 统计概览 -->
        <NGrid :cols="4" :x-gap="16" class="stats-grid">
          <NGridItem>
            <NCard class="stat-card">
              <NStatistic label="相似词总数" :value="similarWords.length" />
            </NCard>
          </NGridItem>
          <NGridItem>
            <NCard class="stat-card">
              <NStatistic label="高度相似 (≥0.85)" :value="highSimilarityWords.length">
                <template #suffix>
                  <NTag type="success" size="tiny">强关联</NTag>
                </template>
              </NStatistic>
            </NCard>
          </NGridItem>
          <NGridItem>
            <NCard class="stat-card">
              <NStatistic label="中度相似 (0.75-0.85)" :value="mediumSimilarityWords.length">
                <template #suffix>
                  <NTag type="info" size="tiny">中关联</NTag>
                </template>
              </NStatistic>
            </NCard>
          </NGridItem>
          <NGridItem>
            <NCard class="stat-card">
              <NStatistic label="一般相似 (<0.75)" :value="lowSimilarityWords.length">
                <template #suffix>
                  <NTag type="warning" size="tiny">弱关联</NTag>
                </template>
              </NStatistic>
            </NCard>
          </NGridItem>
        </NGrid>

        <!-- 详细内容 Tabs -->
        <NTabs type="line" animated class="results-tabs">
          <!-- 网络图 -->
          <NTabPane name="network" tab="关联网络">
            <template #tab>
              <span class="tab-label">
                <NIcon :component="GitNetworkOutline" size="16" />
                关联网络
              </span>
            </template>
            <WordNetworkGraph
              :center-word="searchedWord"
              :similar-words="similarWords"
              @select-word="selectWord"
            />
          </NTabPane>

          <!-- 列表视图 -->
          <NTabPane name="list" tab="详细列表">
            <template #tab>
              <span class="tab-label">
                <NIcon :component="ListOutline" size="16" />
                详细列表
              </span>
            </template>
            <NCard>
              <NList hoverable clickable>
                <NListItem
                  v-for="(item, index) in similarWords"
                  :key="index"
                  @click="selectWord(item.word)"
                >
                  <NThing>
                    <template #header>
                      <span class="word-rank">#{{ index + 1 }}</span>
                      <span class="word-name">{{ item.word }}</span>
                      <NTag
                        :type="getSimilarityType(item.similarity)"
                        size="small"
                        class="similarity-tag"
                      >
                        {{ (item.similarity * 100).toFixed(1) }}%
                      </NTag>
                    </template>
                    <template #description>
                      <NProgress
                        type="line"
                        :percentage="item.similarity * 100"
                        :show-indicator="false"
                        :height="6"
                        :color="getSimilarityColor(item.similarity)"
                        :rail-color="getSimilarityColor(item.similarity) + '30'"
                      />
                    </template>
                    <template #action>
                      <NButton text size="small" @click.stop="selectWord(item.word)">
                        <template #icon>
                          <NIcon :component="ArrowForwardOutline" />
                        </template>
                        探索此词
                      </NButton>
                    </template>
                  </NThing>
                </NListItem>
              </NList>
            </NCard>
          </NTabPane>

          <!-- 相关诗词 -->
          <NTabPane name="poems" tab="相关诗词">
            <template #tab>
              <span class="tab-label">
                <NIcon :component="BookOutline" size="16" />
                相关诗词
                <NBadge :value="relatedPoems.length" :max="99" />
              </span>
            </template>
            <NSpin :show="loadingPoems">
              <NEmpty v-if="!loadingPoems && relatedPoems.length === 0" description="暂无相关诗词" />
              <NGrid v-else :cols="2" :x-gap="16" :y-gap="16">
                <NGridItem v-for="poem in relatedPoems" :key="poem.id">
                  <NCard
                    hoverable
                    class="poem-card"
                    @click="goToPoem(poem.id)"
                  >
                    <template #header>
                      <div class="poem-header">
                        <span class="poem-title">{{ poem.title }}</span>
                        <NTag size="tiny" type="info">{{ poem.dynasty }}</NTag>
                      </div>
                    </template>
                    <div class="poem-author">{{ poem.author }}</div>
                  </NCard>
                </NGridItem>
              </NGrid>
            </NSpin>
          </NTabPane>
        </NTabs>
      </template>
    </section>

    <!-- 使用说明 -->
    <section v-else class="guide-section">
      <NCard title="如何使用词境探索">
        <NGrid :cols="3" :x-gap="24">
          <NGridItem>
            <div class="guide-item">
              <div class="guide-icon">1</div>
              <h4>输入词汇</h4>
              <p>输入任意诗词中的词汇，如"春风"、"明月"、"相思"等</p>
            </div>
          </NGridItem>
          <NGridItem>
            <div class="guide-item">
              <div class="guide-icon">2</div>
              <h4>调整阈值</h4>
              <p>通过滑块调整相似度阈值，发现更多或更精准的关联词</p>
            </div>
          </NGridItem>
          <NGridItem>
            <div class="guide-item">
              <div class="guide-icon">3</div>
              <h4>探索网络</h4>
              <p>查看关联网络图，点击任意词汇继续深入探索</p>
            </div>
          </NGridItem>
        </NGrid>
      </NCard>
    </section>
  </div>
</template>

<style scoped>
.word-similarity-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  padding-bottom: 48px;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 64px 24px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  color: #fff;
  font-size: 42px;
  font-weight: 600;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.hero-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 18px;
  line-height: 1.8;
  margin: 0;
}

.hero-stats {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

/* Search Section */
.search-section {
  max-width: 900px;
  margin: -32px auto 32px;
  padding: 0 24px;
  position: relative;
  z-index: 2;
}

.search-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.search-box {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
}

.search-btn {
  min-width: 120px;
}

.threshold-control {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.threshold-label {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.hot-words {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hot-words-label,
.history-label {
  font-size: 14px;
  color: #888;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.hot-word-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.hot-word-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.search-history {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e0e0e0;
  flex-wrap: wrap;
}

.history-tag {
  cursor: pointer;
}

/* Loading State */
.loading-state {
  text-align: center;
  padding: 64px 24px;
  color: #666;
}

.loading-state p {
  margin-top: 16px;
}

/* Results Section */
.results-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.stats-grid {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  border-radius: 12px;
}

.empty-state {
  padding: 64px 24px;
}

.empty-hint {
  color: #888;
  font-size: 14px;
  margin-top: 8px;
}

.results-tabs {
  margin-top: 24px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Word List */
.word-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #f0f0f0;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  margin-right: 12px;
}

.word-name {
  font-size: 18px;
  font-weight: 500;
  color: #333;
  margin-right: 12px;
}

.similarity-tag {
  font-family: monospace;
}

/* Poem Cards */
.poem-card {
  cursor: pointer;
  transition: all 0.2s;
}

.poem-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.poem-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.poem-title {
  font-weight: 500;
  color: #333;
}

.poem-author {
  color: #666;
  font-size: 14px;
}

/* Guide Section */
.guide-section {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 24px;
}

.guide-item {
  text-align: center;
  padding: 24px;
}

.guide-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  margin: 0 auto 16px;
}

.guide-item h4 {
  font-size: 18px;
  color: #333;
  margin: 0 0 8px;
}

.guide-item p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
