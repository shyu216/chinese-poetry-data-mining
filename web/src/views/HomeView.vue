<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchIndex } from '@/composables/useSearchIndex'
import { NSpace, NInput, NButton, NCard, NTag, NSpin, NEmpty, NRadioGroup, NRadio, NInputGroup } from 'naive-ui'
import { SearchOutline, RefreshOutline } from '@vicons/ionicons5'

const router = useRouter()
const { getRandomKeywordIndex, searchByKeyword, loading } = useSearchIndex()

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

const handleRandomSearch = async () => {
  hasSearched.value = true
  const data = await getRandomKeywordIndex()
  currentKeyword.value = data.keyword
  results.value = data.poems
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  hasSearched.value = true
  currentKeyword.value = searchQuery.value
  results.value = await searchByKeyword(searchQuery.value)
}

const goToPoem = (id: string) => {
  router.push(`/poems/${id}`)
}

const dynastyColors: Record<string, string> = {
  '唐': 'red',
  '宋': 'blue',
  '元': 'green',
  '明': 'yellow',
  '清': 'purple',
  '近现代': 'orange'
}

onMounted(() => {
  handleRandomSearch()
})
</script>

<template>
  <div class="home-view">
    <NCard class="search-card">
      <div class="search-header">
        <h1>诗词数据挖掘</h1>
        <p>基于关键词索引搜索诗词</p>
      </div>
      
      <div class="search-form">
        <NInputGroup>
          <NInput
            v-model:value="searchQuery"
            placeholder="输入关键词搜索..."
            size="large"
            @keyup.enter="handleSearch"
          />
          <NButton type="primary" size="large" @click="handleSearch" :loading="loading">
            <template #icon>
              <SearchOutline />
            </template>
            搜索
          </NButton>
        </NInputGroup>
        
        <div class="random-search">
          <NButton quaternary @click="handleRandomSearch" :loading="loading">
            <template #icon>
              <RefreshOutline />
            </template>
            随机关键词
          </NButton>
        </div>
      </div>

      <div v-if="currentKeyword" class="current-keyword">
        当前关键词: <NTag type="primary">{{ currentKeyword }}</NTag>
      </div>
    </NCard>

    <NCard v-if="hasSearched" title="搜索结果" class="results-card">
      <template #header-extra>
        <span>找到 {{ results.length }} 条结果</span>
      </template>
      
      <NSpin :show="loading">
        <NEmpty v-if="results.length === 0 && !loading" description="未找到匹配的诗词" />
        
        <div v-else class="results-list">
          <div
            v-for="result in results"
            :key="result.id"
            class="result-item"
            @click="goToPoem(result.id)"
          >
            <div class="result-title">{{ result.title }}</div>
            <div class="result-meta">
              <NTag :bordered="false" :type="dynastyColors[result.dynasty] as any" size="small">
                {{ result.dynasty }}
              </NTag>
              <span class="author">{{ result.author }}</span>
            </div>
          </div>
        </div>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 900px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 16px;
}

.search-header {
  text-align: center;
  margin-bottom: 24px;
}

.search-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #c41e3a;
}

.search-header p {
  margin: 0;
  color: #666;
}

.search-form {
  max-width: 600px;
  margin: 0 auto;
}

.random-search {
  margin-top: 12px;
  text-align: center;
}

.current-keyword {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
  text-align: center;
}

.results-card {
  margin-top: 16px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.result-item:hover {
  background-color: #f5f5f5;
}

.result-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.result-meta {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.author {
  color: #666;
  font-size: 14px;
}
</style>
