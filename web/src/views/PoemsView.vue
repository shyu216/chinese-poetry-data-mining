<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePoems } from '@/composables/usePoems'
import { usePoemSearch } from '@/search'
import { useShuffle } from '@/composables/useShuffle'
import type { PoemSummary } from '@/composables/types'
import { NEmpty, NSelect, NButton, NGrid, NGridItem, NSpace, NTooltip } from 'naive-ui'
import {
  BookOutline,
  LibraryOutline,
  FlameOutline,
  SchoolOutline,
  MusicalNotesOutline,
  ShuffleOutline,
  RefreshOutline
} from '@vicons/ionicons5'
import PageHeader from '@/components/layout/PageHeader.vue'
import StatsCard from '@/components/display/StatsCard.vue'
import PoemList from '@/components/display/PoemList.vue'
import { SearchContainer } from '@/components/search'

const router = useRouter()
const { totalPoems, dynasties, genres, poemCounts, loadMetadata, queryPoems } = usePoems()
const { search: searchPoems, isReady: poemSearchReady } = usePoemSearch()

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(24)
const dynastyFilter = ref<string | null>(null)
const genreFilter = ref<string | null>(null)
const pagePoems = ref<PoemSummary[]>([])
const pageTotal = ref(0)
const isInitializing = ref(true)
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: 'memory' })

const dynastyOptions = computed(() => [
  { label: '全部朝代', value: '' },
  ...dynasties.value.map(item => ({ label: item, value: item }))
])

const genreOptions = computed(() => [
  { label: '全部体裁', value: '' },
  ...genres.value.map(item => ({ label: item, value: item }))
])

const isSearchMode = computed(() => searchQuery.value.trim().length > 0)
const { isShuffled, shuffledItems, toggleShuffle, shuffle } = useShuffle({ items: computed(() => pagePoems.value) })
const displayPoems = computed(() => (isSearchMode.value ? pagePoems.value : shuffledItems.value))
const displayTotal = computed(() => pageTotal.value)

async function refreshPage() {
  if (isSearchMode.value) {
    isSearching.value = true
    try {
      const result = await searchPoems(searchQuery.value.trim(), {
        limit: pageSize.value,
        offset: (currentPage.value - 1) * pageSize.value,
        filters: {
          dynasty: dynastyFilter.value || undefined,
          genre: genreFilter.value || undefined
        }
      })
      pagePoems.value = result.items
      pageTotal.value = result.total
      searchStats.value = { queryTime: result.queryTime, source: result.source }
    } finally {
      isSearching.value = false
    }
    return
  }

  const result = await queryPoems(
    {
      dynasty: dynastyFilter.value || undefined,
      genre: genreFilter.value || undefined
    },
    currentPage.value,
    pageSize.value
  )
  pagePoems.value = result.poems
  pageTotal.value = result.filteredTotal
  searchStats.value = { queryTime: 0, source: 'memory' }
}

function goToPoemDetail(poem: PoemSummary) {
  if (poem.chunk_id !== undefined) {
    router.push({ path: `/poems/${poem.id}`, query: { chunk_id: String(poem.chunk_id) } })
    return
  }
  router.push(`/poems/${poem.id}`)
}

function clearFilters() {
  searchQuery.value = ''
  dynastyFilter.value = null
  genreFilter.value = null
  currentPage.value = 1
}

onMounted(async () => {
  try {
    await loadMetadata()
    await refreshPage()
  } finally {
    isInitializing.value = false
  }
})

watch(searchQuery, async () => {
  currentPage.value = 1
  await refreshPage()
})

watch([dynastyFilter, genreFilter], async () => {
  currentPage.value = 1
  await refreshPage()
})

watch([currentPage, pageSize], async () => {
  if (isInitializing.value) return
  await refreshPage()
})
</script>

<template>
  <div class="poems-view">
    <PageHeader
      title="诗词列表 "
      :subtitle="`共收录 ${totalPoems.toLocaleString()} 首诗词，当前结果 ${displayTotal.toLocaleString()} 首`"
      :icon="BookOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard label="诗词总数" :value="totalPoems.toLocaleString()" :prefix-icon="LibraryOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="唐诗" :value="poemCounts.tangshi.toLocaleString()" :prefix-icon="FlameOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="宋诗" :value="poemCounts.songshi.toLocaleString()" :prefix-icon="SchoolOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="宋词" :value="poemCounts.songci.toLocaleString()" :prefix-icon="MusicalNotesOutline" />
      </NGridItem>
    </NGrid>

    <SearchContainer
      v-model="searchQuery"
      placeholder="搜索诗词、作者或内容..."
      :total="displayTotal"
      :query-time="searchStats.queryTime"
      :source="searchStats.source as any"
      :loading="isSearching"
      @clear="clearFilters"
    >
      <template #filters>
        <NSelect v-model:value="dynastyFilter" :options="dynastyOptions" placeholder="朝代" style="width: 130px" clearable />
        <NSelect v-model:value="genreFilter" :options="genreOptions" placeholder="体裁" style="width: 130px" clearable />
        <NSpace>
          <NTooltip trigger="hover">
            <template #trigger>
              <NButton :type="isShuffled ? 'primary' : 'default'" :ghost="!isShuffled" :disabled="isSearchMode" @click="toggleShuffle">
                <template #icon><ShuffleOutline /></template>
                {{ isShuffled ? '已随机' : '随机排序' }}
              </NButton>
            </template>
            仅对当前页结果随机排序
          </NTooltip>
          <NTooltip v-if="isShuffled && !isSearchMode" trigger="hover">
            <template #trigger>
              <NButton @click="shuffle">
                <template #icon><RefreshOutline /></template>
                换一批
              </NButton>
            </template>
            重新随机排序
          </NTooltip>
        </NSpace>
      </template>
    </SearchContainer>

    <NEmpty v-if="isInitializing" description="正在加载诗词数据..." />
    <NEmpty v-else-if="displayPoems.length === 0" description="暂无匹配结果">
      <template #extra>
        <NButton @click="clearFilters">清除筛选</NButton>
      </template>
    </NEmpty>
    <div v-else class="poems-container">
      <PoemList
        :poems="displayPoems"
        :total="displayTotal"
        v-model:page="currentPage"
        v-model:page-size="pageSize"
        :show-pagination="true"
        :grid-view="true"
        @view-poem="goToPoemDetail"
      />
    </div>
  </div>
</template>

<style scoped>
.poems-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.stats-grid {
  margin-bottom: 24px;
}

.poems-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

@media (max-width: 768px) {
  .poems-view {
    padding: 16px;
  }
}
</style>
