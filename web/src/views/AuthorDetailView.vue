<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthors } from '@/composables/useAuthors'
import { usePoems } from '@/composables/usePoems'
import { NCard, NSpin, NEmpty, NTag } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const { loadAllAuthors } = useAuthors()
const { getAllPoems } = usePoems()

const authorName = route.params.name as string
const author = ref<Author | null>(null)
const poems = ref<PoemSummary[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const authors = await loadAllAuthors()
    author.value = authors.find(a => a.author === authorName) || null
    const allPoems = await getAllPoems(undefined, 1, 10000)
    poems.value = allPoems.poems.filter(p => p.author === authorName)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const goToPoem = (id: string) => {
  router.push(`/poems/${id}`)
}

const dynastyColors: Record<string, string> = {
  '唐': 'red',
  '宋': 'blue',
  '元': 'green',
  '明': 'yellow',
  '清': 'purple'
}
</script>

<template>
  <div class="author-detail-view">
    <NCard>
      <NSpin :show="loading">
        <div v-if="author" class="author-header">
          <h1>{{ authorName }}</h1>
          <div class="author-meta">
            <NTag :bordered="false" :type="dynastyColors[author.dynasty] as any" size="large">
              {{ author.dynasty }}
            </NTag>
            <NTag v-for="genre in author.genres" :key="genre" size="large" type="info">
              {{ genre }}
            </NTag>
            <span class="poem-count">创作 {{ author.poem_count }} 首</span>
          </div>
        </div>

        <NEmpty v-if="!loading && !author" description="未找到该作者" />

        <div v-if="poems.length > 0" class="poems-section">
          <h3>作品列表</h3>
          <div class="poems-list">
            <div
              v-for="poem in poems"
              :key="poem.id"
              class="poem-item"
              @click="goToPoem(poem.id)"
            >
              <div class="poem-title">{{ poem.title }}</div>
              <div class="poem-meta">
                <NTag :bordered="false" :type="dynastyColors[poem.dynasty] as any" size="small">
                  {{ poem.dynasty }}
                </NTag>
                <NTag :bordered="false" type="info" size="small">
                  {{ poem.genre }}
                </NTag>
                <span class="poem-type">{{ (poem as any).poem_type }}</span>
              </div>
            </div>
          </div>
        </div>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.author-detail-view {
  max-width: 900px;
  margin: 0 auto;
}

.author-header {
  text-align: center;
  margin-bottom: 24px;
}

.author-header h1 {
  margin: 0 0 16px;
  font-size: 32px;
  color: #c41e3a;
}

.author-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.poem-count {
  color: #666;
  font-size: 16px;
}

.poems-section {
  margin-top: 24px;
}

.poems-section h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #333;
}

.poems-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.poem-item {
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.poem-item:hover {
  background-color: #f5f5f5;
}

.poem-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.poem-meta {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.poem-type {
  color: #666;
  font-size: 14px;
}
</style>
