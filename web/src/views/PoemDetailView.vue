<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePoems } from '@/composables/usePoems'
import { 
  NCard, NSpin, NEmpty, NTag, NButton, NSpace,
  NDivider, NIcon
} from 'naive-ui'
import { 
  ArrowBackOutline, BookOutline, PersonOutline,
  TimeOutline, TextOutline, CopyOutline
} from '@vicons/ionicons5'
import type { PoemDetail } from '@/composables/usePoems'

const route = useRoute()
const router = useRouter()
const { getPoemDetail, loadingChunk } = usePoems()

const poem = ref<PoemDetail | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const id = route.params.id as string
    poem.value = await getPoemDetail(id)
    if (!poem.value) {
      error.value = '未找到该诗词'
    }
  } catch (e) {
    error.value = '加载失败，请稍后重试'
    console.error(e)
  } finally {
    loading.value = false
  }
})

const goBack = () => {
  router.back()
}

const goToAuthor = (author: string) => {
  router.push(`/authors?search=${encodeURIComponent(author)}`)
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
    <NButton quaternary class="back-btn" @click="goBack">
      <template #icon>
        <ArrowBackOutline />
      </template>
      返回列表
    </NButton>

    <NSpin :show="loading || loadingChunk" size="large">
      <NEmpty v-if="error" :description="error">
        <template #extra>
          <NButton @click="goBack">返回</NButton>
        </template>
      </NEmpty>

      <article v-else-if="poem" class="poem-content">
        <header class="poem-header">
          <div class="title-section">
            <h1 class="poem-title">{{ poem.title || '无题' }}</h1>
            <div class="poem-subtitle">
              <span 
                class="dynasty-badge"
                :style="{ 
                  color: getDynastyConfig(poem.dynasty).color,
                  background: getDynastyConfig(poem.dynasty).bg 
                }"
              >
                {{ poem.dynasty }}
              </span>
              <span class="author-name" @click="goToAuthor(poem.author)">
                {{ poem.author }}
              </span>
            </div>
          </div>
          
          <div class="poem-actions">
            <NButton quaternary size="small" @click="copyPoem">
              <template #icon>
                <CopyOutline />
              </template>
              复制
            </NButton>
          </div>
        </header>

        <NDivider />

        <div class="poem-body">
          <p 
            v-for="(sentence, index) in poem.sentences" 
            :key="index"
            class="poem-sentence"
          >
            {{ sentence }}
          </p>
        </div>

        <NDivider />

        <footer class="poem-footer">
          <NSpace align="center" :size="16">
            <NTag v-if="poem.genre" size="medium">
              <template #icon>
                <BookOutline />
              </template>
              {{ poem.genre }}
            </NTag>
            <NTag v-if="poem.poem_type" size="medium" type="info">
              <template #icon>
                <TextOutline />
              </template>
              {{ poem.poem_type }}
            </NTag>
            <NTag v-if="poem.meter_pattern" size="medium" type="success">
              <template #icon>
                <TimeOutline />
              </template>
              {{ poem.meter_pattern }}
            </NTag>
          </NSpace>

          <div v-if="poem.words.length > 0" class="word-cloud">
            <h3 class="section-title">关键词</h3>
            <div class="words-list">
              <NTag 
                v-for="word in poem.words.slice(0, 30)" 
                :key="word"
                size="small"
                :bordered="false"
                class="word-tag"
              >
                {{ word }}
              </NTag>
            </div>
          </div>
        </footer>
      </article>
    </NSpin>
  </div>
</template>

<style scoped>
.poem-detail-view {
  max-width: 800px;
  margin: 0 auto;
}

.back-btn {
  margin-bottom: 16px;
}

.poem-content {
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 32px;
}

.poem-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.title-section {
  flex: 1;
}

.poem-title {
  margin: 0 0 12px;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 32px;
  font-weight: 600;
  color: var(--color-ink);
  line-height: 1.3;
}

.poem-subtitle {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dynasty-badge {
  padding: 4px 10px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 4px;
}

.author-name {
  font-size: 16px;
  color: var(--color-seal);
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.author-name:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.poem-actions {
  flex-shrink: 0;
}

.poem-body {
  padding: 24px 0;
  text-align: center;
}

.poem-sentence {
  margin: 0 0 12px;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 20px;
  line-height: 1.8;
  color: var(--color-ink);
  letter-spacing: 0.05em;
}

.poem-sentence:last-child {
  margin-bottom: 0;
}

.poem-footer {
  padding-top: 8px;
}

.section-title {
  margin: 24px 0 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink-light);
}

.word-cloud {
  margin-top: 24px;
}

.words-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.word-tag {
  transition: all 0.2s ease;
}

.word-tag:hover {
  transform: scale(1.05);
}
</style>
