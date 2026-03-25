<!--
  文件: web/src/views/PoemDetailView.vue
  说明: 诗词详情页，负责按 `id`（可带 chunk_id）加载单首诗词内容并展示详细信息与相关导航操作。

  数据管线:
    - 入口: 路由参数 `id` 与可选 `chunk_id` 触发 `usePoemsV2.getPoemById(id, chunkId)`。
    - 读取: 若提供 chunk_id，则直接从对应分片读取；否则通过索引定位分片后加载并解析分片内容。
    - 渲染: 成功加载后将 `PoemDetail` 对象填充到页面并展示（复制、跳转关键字/作者等功能）。

  复杂度:
    - 单首诗加载为常数读取 O(1)（定位并读取单个分片或记录）；若需加载整个分片，其成本为 O(c)（c = 分片大小）。
    - 页面渲染成本低，主要由诗文句数决定（O(m)，m = 句数）。

  风险/建议:
    - 若分片较大，单次加载与 JSON 解析会阻塞主线程，建议使用流式解析或 Web Worker。
    - 当并发访问多首诗时应注意 chunk 加载的并发控制与缓存重用，避免重复下载。
    - 当前已包含较为详尽的加载阶段日志（console），可扩展为更完整的用户可见错误/重试提示。
-->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePoemsV2 } from '@/composables/usePoemsV2'
import type { PoemDetail } from '@/composables/types'
import {
  NCard, NSpin, NEmpty, NTag, NButton, NSpace,
  NDivider, NGrid, NGridItem
} from 'naive-ui'
import {
  BookOutline, PersonOutline,
  TimeOutline, TextOutline, CopyOutline, ChevronForwardOutline
} from '@vicons/ionicons5'
import { PageHeader } from '@/components/layout'
import { StatsCard } from '@/components/display'
import { useLoading } from '@/composables/useLoading'

import { PoemContent } from '@/components/content'

const loading = useLoading()
const route = useRoute()
const router = useRouter()
const { getPoemById } = usePoemsV2()

const poem = ref<PoemDetail | null>(null)
const error = ref<string | null>(null)

const poemId = computed(() => route.params.id as string)
const chunkId = computed(() => {
  const cid = route.query.chunk_id
  return cid ? parseInt(cid as string, 10) : undefined
})

onMounted(async () => {
  await loadPoemData()
})

const loadPoemData = async () => {
  console.log('[PoemDetailView] loadPoemData START')
  loading.startBlocking('诗词详情', '正在加载诗词详情...')
  error.value = null

  try {
    loading.updatePhase('data', '正在读取诗词内容...')
    console.log('[PoemDetailView] Calling getPoemById...')
    poem.value = await getPoemById(poemId.value, chunkId.value)
    console.log('[PoemDetailView] getPoemById returned:', poem.value ? 'found' : 'not found')

    if (!poem.value) {
      error.value = '未找到该诗词'
      loading.error('未找到该诗词')
      return
    }

    loading.updatePhase('complete', '加载完成')
    setTimeout(() => loading.finish(), 300)
  } catch (e) {
    error.value = '加载失败，请稍后重试'
    loading.error('加载失败')
    console.error(e)
  }
  console.log('[PoemDetailView] loadPoemData END')
}

const goBack = () => {
  router.back()
}

const goToPoems = () => {
  router.push('/poems')
}

const goToAuthor = (author: string) => {
  router.push(`/authors/${encodeURIComponent(author)}`)
}

const goToKeyword = (word: string) => {
  router.push(`/keyword/${encodeURIComponent(word)}`)
}

const copyPoem = () => {
  if (!poem.value) return
  const text = `${poem.value.title}\n${poem.value.author}〔${poem.value.dynasty}〕\n\n${poem.value.sentences.join('\n')}`
  navigator.clipboard.writeText(text)
}

const dynastyConfig: Record<string, { color: string; bg: string; icon: string }> = {
  '唐': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', icon: '盛' },
  '宋': { color: '#1E40AF', bg: 'rgba(30, 64, 175, 0.08)', icon: '雅' },
  '元': { color: '#047857', bg: 'rgba(4, 120, 87, 0.08)', icon: '曲' },
  '明': { color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)', icon: '文' },
  '清': { color: '#7C3AED', bg: 'rgba(124, 58, 237, 0.08)', icon: '韵' },
  '近现代': { color: '#DC2626', bg: 'rgba(220, 38, 38, 0.08)', icon: '新' }
}

const getDynastyConfig = (dynasty: string) => {
  return dynastyConfig[dynasty] || { color: '#5C5244', bg: 'rgba(92, 82, 68, 0.08)', icon: '古' }
}
</script>

<template>
  <div class="poem-detail-view">
    <PageHeader
      title="诗词详情"
      subtitle="查看诗词完整内容及作者信息"
      :icon="BookOutline"
    />

      <NEmpty v-if="error" :description="error">
        <template #extra>
          <NButton @click="goToPoems">返回诗词列表</NButton>
        </template>
      </NEmpty>

      <template v-else-if="poem">
        <NCard class="poem-header-card">
          <div class="poem-header">
            <div class="poem-title-section">
              <h1 class="poem-title">{{ poem.title || '无题' }}</h1>
              <div class="poem-subtitle">
                <span
                  class="dynasty-badge"
                  :style="{
                    color: getDynastyConfig(poem.dynasty).color,
                    background: getDynastyConfig(poem.dynasty).bg
                  }"
                >
                  {{ poem.dynasty || '未知' }}
                </span>
                <span class="author-link" @click="goToAuthor(poem.author)">
                  {{ poem.author }}
                  <ChevronForwardOutline class="link-icon" />
                </span>
              </div>
            </div>
          </div>
        </NCard>

        <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
          <NGridItem>
            <StatsCard
              label="朝代"
              :value="poem.dynasty || '未知'"
              :prefix-icon="TimeOutline"
            />
          </NGridItem>
          <NGridItem>
            <StatsCard
              label="体裁"
              :value="poem.genre || '未知'"
              :prefix-icon="BookOutline"
            />
          </NGridItem>
          <NGridItem>
            <StatsCard
              label="类型"
              :value="poem.poem_type || '未知'"
              :prefix-icon="TextOutline"
            />
          </NGridItem>
          <NGridItem>
            <StatsCard
              label="句数"
              :value="poem.sentences.length"
              :prefix-icon="TextOutline"
            />
          </NGridItem>
        </NGrid>

        <PoemContent
          :sentences="poem.sentences"
          :title="poem.title"
          :author="poem.author"
          :dynasty="poem.dynasty"
          :genre="poem.genre"
          mode="text"
          :show-meters="true"
          :show-controls="true"
        />

        <NCard v-if="poem.words.length > 0" title="关键词" class="words-card">
          <div class="words-list">
            <NTag
              v-for="word in poem.words"
              :key="word"
              size="medium"
              :bordered="false"
              class="word-tag"
              @click="goToKeyword(word)"
            >
              {{ word }}
            </NTag>
          </div>
        </NCard>

        <NCard class="author-card" @click="goToAuthor(poem.author)">
          <div class="author-link-section">
            <div class="author-avatar">
              <span class="avatar-text">{{ poem.author.charAt(0) }}</span>
            </div>
            <div class="author-info">
              <h3 class="author-name">{{ poem.author }}</h3>
              <p class="author-hint">点击查看该作者的所有作品</p>
            </div>
            <ChevronForwardOutline class="arrow-icon" />
          </div>
        </NCard>
      </template>
  
  </div>
</template>

<style scoped>
.poem-detail-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.poem-header-card {
  margin-top: 24px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.poem-header {
  text-align: center;
  padding: 24px 0;
}

.poem-title {
  margin: 0 0 16px;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 36px;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.4;
}

.poem-subtitle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.dynasty-badge {
  padding: 6px 14px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 6px;
}

.author-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 18px;
  color: #8b2635;
  cursor: pointer;
  transition: all 0.2s ease;
}

.author-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.link-icon {
  width: 16px;
  height: 16px;
}

.stats-grid {
  margin-bottom: 24px;
}

.words-card {
  margin-bottom: 24px;
}

.words-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.word-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(139, 38, 53, 0.08);
  color: #8b2635;
}

.word-tag:hover {
  transform: scale(1.05);
  background: rgba(139, 38, 53, 0.15);
}

.author-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.author-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.author-link-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.author-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b2635 0%, #c41e3a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
}

.author-info {
  flex: 1;
}

.author-name {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.author-hint {
  margin: 0;
  font-size: 13px;
  color: #999;
}

.arrow-icon {
  width: 20px;
  height: 20px;
  color: #999;
  transition: all 0.2s ease;
}

.author-card:hover .arrow-icon {
  color: #8b2635;
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .poem-title {
    font-size: 28px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
