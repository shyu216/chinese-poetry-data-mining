<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePoems } from '@/composables/usePoems'
import { NCard, NSpin, NEmpty, NPagination, NSelect, NSpace, NTag } from 'naive-ui'
import type { PoemSummary } from '@/composables/usePoems'

const router = useRouter()
const { loadSummary, loading, error } = usePoems()

const poems = ref<PoemSummary[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dynastyFilter = ref<string | null>(null)
const genreFilter = ref<string | null>(null)

const dynasties = [
  { label: '全部', value: null },
  { label: '唐', value: '唐' },
  { label: '宋', value: '宋' },
  { label: '元', value: '元' },
  { label: '明', value: '明' },
  { label: '清', value: '清' }
]

const genres = [
  { label: '全部', value: null },
  { label: '诗', value: '诗' },
  { label: '词', value: '词' },
  { label: '曲', value: '曲' }
]

const filteredPoems = ref<PoemSummary[]>([])

onMounted(async () => {
  try {
    const data = await loadSummary()
    poems.value = data.poems
    total.value = data.metadata.total
    applyFilters()
  } catch (e) {
    console.error(e)
  }
})

const applyFilters = () => {
  let result = poems.value
  
  if (dynastyFilter.value) {
    result = result.filter(p => p.dynasty === dynastyFilter.value)
  }
  if (genreFilter.value) {
    result = result.filter(p => p.genre === genreFilter.value)
  }
  
  filteredPoems.value = result
  total.value = result.length
  page.value = 1
}

const paginatedPoems = () => {
  const start = (page.value - 1) * pageSize.value
  return filteredPoems.value.slice(start, start + pageSize.value)
}

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

const handlePageChange = (p: number) => {
  page.value = p
}
</script>

<template>
  <div class="poets-view">
    <NCard title="诗词浏览">
      <div class="filters">
        <NSpace>
          <NSelect
            v-model:value="dynastyFilter"
            :options="dynasties"
            placeholder="朝代"
            style="width: 120px"
            @update:value="applyFilters"
          />
          <NSelect
            v-model:value="genreFilter"
            :options="genres"
            placeholder="体裁"
            style="width: 120px"
            @update:value="applyFilters"
          />
        </NSpace>
      </div>

      <NSpin :show="loading">
        <NEmpty v-if="filteredPoems.length === 0 && !loading" description="暂无数据" />
        
        <div v-else class="poems-list">
          <div
            v-for="poem in paginatedPoems()"
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
              <span class="author">{{ poem.author }}</span>
              <span class="poem-type">{{ poem.poem_type }}</span>
            </div>
          </div>
        </div>

        <div v-if="filteredPoems.length > 0" class="pagination-wrapper">
          <NPagination
            v-model:page="page"
            :page-size="pageSize"
            :total="total"
            @update:page="handlePageChange"
          />
        </div>
      </NSpin>
    </NCard>
  </div>
</template>

<style scoped>
.poets-view {
  max-width: 900px;
  margin: 0 auto;
}

.filters {
  margin-bottom: 16px;
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
  flex-wrap: wrap;
}

.author, .poem-type {
  color: #666;
  font-size: 14px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
