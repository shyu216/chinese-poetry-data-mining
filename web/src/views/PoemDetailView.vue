<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePoems } from '@/composables/usePoems'
import { NCard, NSpin, NEmpty, NTag, NButton } from 'naive-ui'
import { ArrowBackOutline } from '@vicons/ionicons5'
import type { PoemDetail } from '@/composables/usePoems'

const route = useRoute()
const router = useRouter()
const { getPoem } = usePoems()

const poem = ref<PoemDetail | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const id = route.params.id as string
    poem.value = await getPoem(id)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const goBack = () => {
  router.back()
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
  <div class="poem-detail-view">
    <NCard>
      <template #header>
        <div class="header-actions">
          <NButton quaternary @click="goBack">
            <template #icon>
              <ArrowBackOutline />
            </template>
            返回
          </NButton>
        </div>
      </template>

      <NSpin :show="loading">
        <div v-if="poem" class="poem-content">
          <h1 class="poem-title">{{ poem.title }}</h1>
          
          <div class="poem-meta">
            <NTag :bordered="false" :type="dynastyColors[poem.dynasty] as any">
              {{ poem.dynasty }}
            </NTag>
            <NTag type="info">
              {{ poem.genre }}
            </NTag>
            <span class="author">{{ poem.author }}</span>
            <span class="poem-type">{{ poem.poem_type }}</span>
          </div>

          <div class="poem-body">
            <p v-for="(line, index) in poem.sentences_simplified.split('。').filter(l => l)" :key="index">
              {{ line }}。
            </p>
          </div>

          <div v-if="poem.meter_pattern" class="meter-pattern">
            <strong>格律：</strong>{{ poem.meter_pattern }}
          </div>
        </div>

        <NEmpty v-if="!loading && !poem" description="未找到该诗词" />
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.poem-detail-view {
  max-width: 800px;
  margin: 0 auto;
}

.header-actions {
  display: flex;
  align-items: center;
}

.poem-content {
  text-align: center;
}

.poem-title {
  margin: 0 0 16px;
  font-size: 36px;
  color: #c41e3a;
}

.poem-meta {
  margin-bottom: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.author {
  font-size: 18px;
  color: #333;
}

.poem-type {
  color: #666;
  font-size: 14px;
}

.poem-body {
  font-size: 20px;
  line-height: 2;
  color: #333;
  text-align: center;
  margin-bottom: 24px;
}

.poem-body p {
  margin: 0 0 8px;
}

.meter-pattern {
  padding-top: 16px;
  border-top: 1px solid #eee;
  color: #666;
  font-size: 14px;
}
</style>
