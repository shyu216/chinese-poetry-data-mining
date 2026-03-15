<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthors } from '@/composables/useAuthors'
import { NCard, NSpin, NEmpty, NPagination, NTag } from 'naive-ui'

const router = useRouter()
const { getTopAuthors, loading } = useAuthors()

interface AuthorItem {
  name: string
  dynasty: string
  poem_count: number
  genres: string[]
}

const authors = ref<AuthorItem[]>([])
const page = ref(1)
const pageSize = ref(30)
const total = ref(0)

onMounted(async () => {
  try {
    const data = await getTopAuthors(200)
    authors.value = data
    total.value = data.length
  } catch (e) {
    console.error(e)
  }
})

const paginatedAuthors = () => {
  const start = (page.value - 1) * pageSize.value
  return authors.value.slice(start, start + pageSize.value)
}

const goToAuthor = (name: string) => {
  router.push(`/authors/${encodeURIComponent(name)}`)
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
  <div class="authors-view">
    <NCard title="作者排行榜">
      <template #header-extra>
        <span>共 {{ total }} 位作者</span>
      </template>

      <NSpin :show="loading">
        <NEmpty v-if="authors.length === 0 && !loading" description="暂无数据" />
        
        <div v-else class="authors-list">
          <div
            v-for="(author, index) in paginatedAuthors()"
            :key="author.name"
            class="author-item"
            @click="goToAuthor(author.name)"
          >
            <div class="rank">{{ (page - 1) * pageSize + index + 1 }}</div>
            <div class="author-info">
              <div class="author-name">{{ author.name }}</div>
              <div class="author-meta">
                <NTag :bordered="false" :type="dynastyColors[author.dynasty] as any" size="small">
                  {{ author.dynasty }}
                </NTag>
                <span class="poem-count">{{ author.poem_count }} 首</span>
                <NTag v-for="genre in author.genres" :key="genre" size="small" type="info">
                  {{ genre }}
                </NTag>
              </div>
            </div>
          </div>
        </div>

        <div v-if="authors.length > 0" class="pagination-wrapper">
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
.authors-view {
  max-width: 900px;
  margin: 0 auto;
}

.authors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.author-item {
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 16px;
}

.author-item:hover {
  background-color: #f5f5f5;
}

.rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #c41e3a;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.author-info {
  flex: 1;
}

.author-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.author-meta {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.poem-count {
  color: #666;
  font-size: 14px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
