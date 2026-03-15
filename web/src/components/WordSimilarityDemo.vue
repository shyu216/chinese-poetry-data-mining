<!--
  词相似度演示组件
  展示如何使用 useWordSimilarity composable
-->
<template>
  <div class="word-similarity-demo">
    <h2>词相似度查询</h2>

    <!-- 状态显示 -->
    <div class="status-bar">
      <n-tag v-if="isLoading" type="warning">加载中...</n-tag>
      <n-tag v-else-if="error" type="error">{{ error }}</n-tag>
      <n-tag v-else-if="isReady" type="success">
        已加载 ({{ vocabSize.toLocaleString() }} 个词)
      </n-tag>
    </div>

    <!-- 搜索框 -->
    <div class="search-section">
      <n-input-group>
        <n-input
          v-model:value="searchWord"
          placeholder="输入要查询的词，如：春风"
          @keyup.enter="handleSearch"
          :disabled="!isReady"
        />
        <n-button
          type="primary"
          @click="handleSearch"
          :loading="searching"
          :disabled="!isReady || !searchWord"
        >
          查询
        </n-button>
      </n-input-group>

      <n-slider
        v-model:value="minSimilarity"
        :min="0.5"
        :max="1"
        :step="0.05"
        :marks="{
          0.5: '0.5',
          0.7: '0.7',
          0.8: '0.8',
          0.9: '0.9',
          1: '1.0'
        }"
        style="margin-top: 16px"
      />
      <div class="similarity-label">
        最小相似度: {{ minSimilarity.toFixed(2) }}
      </div>
    </div>

    <!-- 结果展示 -->
    <div v-if="results.length > 0" class="results-section">
      <h3>"{{ searchedWord }}" 的相似词</h3>
      <n-list>
        <n-list-item v-for="(item, index) in results" :key="index">
          <n-thing>
            <template #header>
              <span class="word">{{ item.word }}</span>
              <n-tag
                :type="getSimilarityTagType(item.similarity)"
                size="small"
                style="margin-left: 8px"
              >
                {{ (item.similarity * 100).toFixed(2) }}%
              </n-tag>
            </template>
            <template #description>
              <n-progress
                type="line"
                :percentage="item.similarity * 100"
                :show-indicator="false"
                :height="4"
                :color="getSimilarityColor(item.similarity)"
              />
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </div>

    <n-empty v-else-if="searchedWord && !searching" description="未找到相似词" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  NInput,
  NInputGroup,
  NButton,
  NTag,
  NSlider,
  NList,
  NListItem,
  NThing,
  NProgress,
  NEmpty
} from 'naive-ui'
import { useWordSimilarity } from '@/composables/useWordSimilarity'

// 使用 composable
const {
  isReady,
  isLoading,
  error,
  vocabSize,
  getSimilarWords
} = useWordSimilarity()

// 本地状态
const searchWord = ref('')
const searchedWord = ref('')
const minSimilarity = ref(0.7)
const results = ref<{ word: string; similarity: number }[]>([])
const searching = ref(false)

// 搜索处理
async function handleSearch() {
  if (!searchWord.value.trim()) return

  searching.value = true
  searchedWord.value = searchWord.value.trim()

  try {
    results.value = await getSimilarWords(searchedWord.value, minSimilarity.value)
  } catch (err) {
    console.error('Search failed:', err)
    results.value = []
  } finally {
    searching.value = false
  }
}

// 根据相似度获取标签类型
function getSimilarityTagType(similarity: number): 'success' | 'warning' | 'info' | 'error' {
  if (similarity >= 0.9) return 'success'
  if (similarity >= 0.8) return 'warning'
  if (similarity >= 0.7) return 'info'
  return 'error'
}

// 根据相似度获取进度条颜色
function getSimilarityColor(similarity: number): string {
  if (similarity >= 0.9) return '#18a058'
  if (similarity >= 0.8) return '#f0a020'
  if (similarity >= 0.7) return '#2080f0'
  return '#d03050'
}
</script>

<style scoped>
.word-similarity-demo {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
}

.status-bar {
  margin-bottom: 16px;
}

.search-section {
  margin-bottom: 24px;
}

.similarity-label {
  text-align: center;
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}

.results-section h3 {
  margin-bottom: 16px;
  color: #333;
}

.word {
  font-size: 16px;
  font-weight: 500;
}
</style>
