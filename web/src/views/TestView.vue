<script setup lang="ts">
import { ref } from 'vue'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import { useAuthorsV2 } from '@/composables/useAuthorsV2'
import { useWordcountV2 } from '@/composables/useWordcountV2'
import { useSearchIndexV2 } from '@/composables/useSearchIndexV2'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { usePoemsMetadata } from '@/composables/useMetadataLoader'
import { useAuthorsMetadata } from '@/composables/useMetadataLoader'
import { useWordcountMetadata } from '@/composables/useMetadataLoader'
import { usePoemIndexManifest } from '@/composables/useMetadataLoader'
import { useWordSimilarityMetadata } from '@/composables/useMetadataLoader'

const poemsV2 = usePoemsV2()
const authorsV2 = useAuthorsV2()
const wordcountV2 = useWordcountV2()
const searchIndexV2 = useSearchIndexV2()
const wordSimilarityV2 = useWordSimilarityV2()

const poemsMeta = usePoemsMetadata()
const authorsMeta = useAuthorsMetadata()
const wordcountMeta = useWordcountMetadata()
const poemIndexMeta = usePoemIndexManifest()
const wordSimMeta = useWordSimilarityMetadata()

const log = (msg: string, data?: unknown) => {
  console.log(`[TestView] ${msg}`, data || '')
}

const loadAllMetadata = async () => {
  log('=== 加载所有索引文件元数据 ===')
  
  const poemsIndex = await poemsMeta.loadMetadata()
  log('诗词 CSV 索引:', poemsIndex)
  log('诗词 chunk 数量:', poemsIndex?.metadata?.chunks)
  
  const authorsIndex = await authorsMeta.loadMetadata()
  log('诗人 FBS 索引:', authorsIndex)
  log('诗人 chunk 数量:', authorsIndex?.chunks?.length)
  
  const wordCountIndex = await wordcountMeta.loadMetadata()
  log('词频 JSON 索引:', wordCountIndex)
  log('词频 chunk 数量:', wordCountIndex?.total_chunks)
  
  const poemIndex = await poemIndexMeta.loadMetadata()
  log('诗 index FBS 索引:', poemIndex)
  log('诗 index 文件数量:', poemIndex?.metadata?.indexFiles)
  
  const wordSimIndex = await wordSimMeta.loadMetadata()
  log('词语相似度索引:', wordSimIndex)
  log('词语相似度 chunk 数量:', wordSimIndex?.total_chunks)
  
  log('=== 元数据加载完成 ===')
}

const testPoems = async () => {
  log('测试 usePoemsV2...')
  log('poems loading:', poemsV2.indexLoading.value)
  
  await poemsV2.loadMetadata()
  log('totalPoems:', poemsV2.totalPoems.value)
  log('dynasties:', poemsV2.dynasties.value)
  log('genres:', poemsV2.genres.value)
  
  if (poemsV2.totalChunks.value > 0) {
    const poems = await poemsV2.loadChunkSummaries(0)
    log('加载的第一首诗词:', poems[0])
    
    const details = await poemsV2.loadChunkDetails(0)
    const firstPoem = Array.from(details.values())[0]
    log('诗词详情:', firstPoem)
  }
}

const testAuthors = async () => {
  log('测试 useAuthorsV2...')
  log('authors loading:', authorsV2.loading.value)
  
  await authorsV2.loadMetadata()
  log('totalAuthors:', authorsV2.totalAuthors.value)
  log('totalChunks:', authorsV2.totalChunks.value)
  
  if (authorsV2.totalChunks.value > 0) {
    const authors = await authorsV2.loadAuthorChunk(0)
    log('加载的第一位诗人:', authors[0])
  }
}

const testWordcount = async () => {
  log('测试 useWordcountV2...')
  log('wordcount loading:', wordcountV2.loading.value)
  
  await wordcountV2.loadMetadata()
  log('totalWords:', wordcountV2.totalWords.value)
  log('totalChunks:', wordcountV2.totalChunks.value)
  
  const topWords = await wordcountV2.getTopWords(5)
  log('top words:', topWords)
}

const testSearchIndex = async () => {
  log('测试 useSearchIndexV2...')
  log('searchIndex loading:', searchIndexV2.loading.value)
  
  await searchIndexV2.loadMetadata()
  log('totalPoems:', searchIndexV2.totalPoems.value)
  
  const results = await searchIndexV2.searchByKeyword('明月', { limit: 5 })
  log('搜索"明月"结果:', results)
}

const testWordSimilarity = async () => {
  log('测试 useWordSimilarityV2...')
  log('wordSimilarity loading:', wordSimilarityV2.loading.value)
  
  await wordSimilarityV2.loadMetadata()
  log('vocabSize:', wordSimilarityV2.vocabSize.value)
  
  await wordSimilarityV2.loadVocab()
  log('vocab loaded')
  
  const similar = await wordSimilarityV2.getSimilarWords('清风', { maxResults: 5 })
  log('查找"清风"相似词:', similar)
}

const testAll = async () => {
  log('=== 开始测试所有 composables_v2 ===')
  
  await testPoems()
  await testAuthors()
  await testWordcount()
  await testSearchIndex()
  await testWordSimilarity()
  
  log('=== 测试完成 ===')
}
</script>

<template>
  <div class="test-view">
    <h1>Composables V2 测试</h1>
    
    <div class="test-section">
      <h2>状态概览</h2>
      
      <div class="status-grid">
        <div class="status-item">
          <span class="label">诗词总数:</span>
          <span class="value">{{ poemsV2.totalPoems.value }}</span>
        </div>
        <div class="status-item">
          <span class="label">诗词分块:</span>
          <span class="value">{{ poemsV2.totalChunks.value }}</span>
        </div>
        <div class="status-item">
          <span class="label">诗人总数:</span>
          <span class="value">{{ authorsV2.totalAuthors.value }}</span>
        </div>
        <div class="status-item">
          <span class="label">诗人分块:</span>
          <span class="value">{{ authorsV2.totalChunks.value }}</span>
        </div>
        <div class="status-item">
          <span class="label">词频加载:</span>
          <span class="value">{{ wordcountV2.loading.value ? '加载中...' : (wordcountV2.totalWords.value || '待加载') }}</span>
        </div>
        <div class="status-item">
          <span class="label">搜索索引:</span>
          <span class="value">{{ searchIndexV2.loading.value ? '加载中...' : (searchIndexV2.totalPoems.value || '待加载') }}</span>
        </div>
        <div class="status-item">
          <span class="label">词语相似度:</span>
          <span class="value">{{ wordSimilarityV2.loading.value ? '加载中...' : (wordSimilarityV2.vocabSize.value || '待加载') }}</span>
        </div>
      </div>
    </div>
    
    <div class="test-section">
      <h2>索引文件 Chunk 数量</h2>
      
      <div class="status-grid">
        <div class="status-item">
          <span class="label">诗词 CSV:</span>
          <span class="value">{{ poemsMeta.metadata.value?.metadata?.chunks || '待加载' }}</span>
        </div>
        <div class="status-item">
          <span class="label">诗人 FBS:</span>
          <span class="value">{{ authorsMeta.metadata.value?.chunks?.length || '待加载' }}</span>
        </div>
        <div class="status-item">
          <span class="label">词频 JSON:</span>
          <span class="value">{{ wordcountMeta.metadata.value?.total_chunks || '待加载' }}</span>
        </div>
        <div class="status-item">
          <span class="label">诗 index FBS:</span>
          <span class="value">{{ poemIndexMeta.metadata.value?.metadata?.indexFiles || '待加载' }}</span>
        </div>
        <div class="status-item">
          <span class="label">词语相似度:</span>
          <span class="value">{{ wordSimMeta.metadata.value?.total_chunks || '待加载' }}</span>
        </div>
      </div>
    </div>
    
    <div class="test-section">
      <h2>测试按钮</h2>
      <div class="button-group">
        <button @click="loadAllMetadata" class="test-btn primary">加载所有索引元数据</button>
        <button @click="testAll" class="test-btn">运行全部测试</button>
        <button @click="testPoems" class="test-btn">测试诗词</button>
        <button @click="testAuthors" class="test-btn">测试诗人</button>
        <button @click="testWordcount" class="test-btn">测试词频</button>
        <button @click="testSearchIndex" class="test-btn">测试搜索</button>
        <button @click="testWordSimilarity" class="test-btn">测试相似度</button>
      </div>
    </div>
    
    <div class="test-section">
      <h2>说明</h2>
      <p>点击上方按钮测试各个 composable。测试结果会在控制台输出。</p>
      <p>请打开浏览器开发者工具 (F12) 查看 Console 日志。</p>
    </div>
  </div>
</template>

<style scoped>
.test-view {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  font-family: "Noto Serif SC", serif;
  font-size: 28px;
  color: var(--color-ink);
  margin-bottom: 32px;
}

h2 {
  font-family: "Noto Serif SC", serif;
  font-size: 18px;
  color: var(--color-ink);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.test-section {
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 24px;
  margin-bottom: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-bg);
  border-radius: 4px;
}

.status-item .label {
  color: var(--color-ink-light);
  font-size: 14px;
}

.status-item .value {
  color: var(--color-seal);
  font-weight: 600;
  font-size: 14px;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.test-btn {
  padding: 10px 20px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-ink);
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.test-btn:hover {
  background: rgba(139, 38, 53, 0.08);
  border-color: var(--color-seal);
  color: var(--color-seal);
}

.test-btn.primary {
  background: var(--color-seal);
  color: #fff;
  border-color: var(--color-seal);
}

.test-btn.primary:hover {
  background: var(--color-seal-light);
}
</style>
