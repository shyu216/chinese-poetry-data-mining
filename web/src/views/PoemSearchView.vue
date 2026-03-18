<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchIndexV2 } from '@/composables/useSearchIndexV2'
import { useMetadataLoader, POEM_INDEX_STORAGE } from '@/composables/useMetadataLoader'
import { getCache } from '@/composables/useCacheV2'
import type { SearchResult, SearchResultSet } from '@/composables/types'
import {
  NCard, NSpin, NEmpty, NSelect, NSpace, NTag,
  NButton, NInput, NPagination, NGrid, NGridItem,
  NAlert
} from 'naive-ui'
import {
  SearchOutline, FilterOutline, BookOutline,
  PersonOutline, TimeOutline, LibraryOutline,
  FlameOutline, SchoolOutline, MusicalNotesOutline,
  ChevronForwardOutline
} from '@vicons/ionicons5'
import PageHeader from '@/components/PageHeader.vue'
import StatsCard from '@/components/StatsCard.vue'
import ChunkLoaderStatus from '@/components/ChunkLoaderStatus.vue'

const router = useRouter()
const searchIndexV2 = useSearchIndexV2()
const poemIndexMeta = useMetadataLoader<any>('poemIndex')

const results = ref<SearchResult[]>([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = ref(24)
const searchQuery = ref('')
const isSearching = ref(false)
const queryTime = ref(0)
const isInitializing = ref(true)

const loadedPrefixCount = ref(0)
const totalPrefixCount = ref(0)

const dynastyFilter = ref<string | null>(null)
const genreFilter = ref<string | null>(null)

const dynastyOptions = computed(() => [
  { label: '全部朝代', value: '' },
  { label: '唐', value: '唐' },
  { label: '宋', value: '宋' }
])

const genreOptions = computed(() => [
  { label: '全部体裁', value: '' },
  { label: '诗', value: '诗' },
  { label: '词', value: '词' }
])

const totalPoems = computed(() => searchIndexV2.totalPoems.value || 0)
const isFullyLoaded = computed(() => loadedPrefixCount.value >= totalPrefixCount.value && totalPrefixCount.value > 0)

const isLoading = computed(() => isInitializing.value || isSearching.value)

const loadStats = async () => {
  try {
    const manifest = await poemIndexMeta.loadMetadata()
    const prefixes = Object.keys(manifest?.prefixMap || {})
    totalPrefixCount.value = prefixes.length

    const loadedPrefixes = await getCache<string[]>(POEM_INDEX_STORAGE, 'loaded-prefixes')
    if (loadedPrefixes) {
      loadedPrefixCount.value = loadedPrefixes.length
    }
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

const doSearch = async () => {
  if (!searchQuery.value.trim() && !dynastyFilter.value && !genreFilter.value) {
    results.value = []
    totalCount.value = 0
    return
  }

  isSearching.value = true
  const startTime = performance.now()

  try {
    let searchResults: SearchResult[]

    if (searchQuery.value.trim()) {
      searchResults = await searchIndexV2.searchByKeyword(searchQuery.value.trim(), {
        dynasty: dynastyFilter.value || undefined,
        limit: 1000
      })
    } else if (dynastyFilter.value) {
      const resultSet = await searchIndexV2.getPoemsByDynasty(
        dynastyFilter.value,
        1,
        1000
      )
      searchResults = resultSet.results
    } else {
      searchResults = []
      const manifest = await searchIndexV2.loadMetadata()
      const prefixes = Object.keys(manifest?.prefixMap || {})

      for (const prefix of prefixes) {
        const poems = await searchIndexV2.getPoemsByPrefix(prefix, 100)
        searchResults.push(...poems.map(p => ({
          id: p.id,
          title: p.title,
          author: p.author,
          dynasty: p.dynasty,
          score: 1
        })))
      }

      if (genreFilter.value) {
        searchResults = searchResults.filter((_, i) => i < 1000)
      }
    }

    if (genreFilter.value && searchQuery.value.trim()) {
      searchResults = searchResults.filter(r => {
        return r.dynasty === (dynastyFilter.value || r.dynasty)
      })
    }

    totalCount.value = searchResults.length
    const start = (page.value - 1) * pageSize.value
    results.value = searchResults.slice(start, start + pageSize.value)
  } catch (e) {
    console.error('Search failed:', e)
    results.value = []
    totalCount.value = 0
  } finally {
    queryTime.value = Math.round(performance.now() - startTime)
    isSearching.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  doSearch()
}

const handlePageChange = (p: number) => {
  page.value = p
  doSearch()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  page.value = 1
  doSearch()
}

const goToPoem = (id: string) => {
  router.push(`/poems/${id}`)
}

const clearFilters = () => {
  dynastyFilter.value = null
  genreFilter.value = null
  searchQuery.value = ''
  page.value = 1
  results.value = []
  totalCount.value = 0
}

const loadingHint = computed(() => {
  if (isFullyLoaded.value) {
    return '已加载全部索引数据'
  }
  return '正在加载诗词索引...'
})

onMounted(async () => {
  await loadStats()
  await searchIndexV2.loadMetadata()
  isInitializing.value = false
})
</script>

<template>
  <div class="poem-search-view">
    <PageHeader
      title="诗词检索"
      subtitle="基于33万首诗词的快速搜索"
      :icon="SearchOutline"
    />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard
          label="总收录诗词"
          :value="`${totalPoems.toLocaleString()}`"
          :prefix-icon="LibraryOutline"
        />
      </NGridItem>
      <NGridItem>
        <StatsCard
          label="搜索耗时"
          :value="queryTime ? `${queryTime}ms` : '-'"
          :prefix-icon="TimeOutline"
        />
      </NGridItem>
    </NGrid>

    <ChunkLoaderStatus
      v-if="!isFullyLoaded && totalPrefixCount > 0"
      :is-loading="false"
      :is-paused="false"
      :progress="Math.round((loadedPrefixCount / totalPrefixCount) * 100)"
      :loaded-count="loadedPrefixCount"
      :total-count="totalPrefixCount"
      title="加载索引数据"
      :hint="loadingHint"
      :stats="[]"
    />

    <NCard class="search-card">
      <NSpace vertical size="large">
        <NSpace align="center" :size="12">
          <NInput
            v-model:value="searchQuery"
            placeholder="搜索标题、作者..."
            style="flex: 1; max-width: 400px"
            size="large"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <SearchOutline />
            </template>
          </NInput>
          <NButton
            type="primary"
            size="large"
            :loading="isSearching"
            @click="handleSearch"
          >
            搜索
          </NButton>
        </NSpace>

        <NSpace align="center" :size="12">
          <span style="color: var(--n-text-color-3); font-size: 14px">
            <FilterOutline style="margin-right: 4px; vertical-align: middle" />
            筛选:
          </span>
          <NSelect
            v-model:value="dynastyFilter"
            :options="dynastyOptions"
            placeholder="朝代"
            style="width: 130px"
            size="medium"
            clearable
            @update:value="handleSearch"
          />
          <NSelect
            v-model:value="genreFilter"
            :options="genreOptions"
            placeholder="体裁"
            style="width: 130px"
            size="medium"
            clearable
            @update:value="handleSearch"
          />
          <NButton
            v-if="searchQuery || dynastyFilter || genreFilter"
            text
            @click="clearFilters"
          >
            清除筛选
          </NButton>
        </NSpace>

        <NAlert v-if="totalCount > 0" type="info" :show-icon="false">
          找到 {{ totalCount.toLocaleString() }} 条结果
        </NAlert>
      </NSpace>
    </NCard>

    <NSpin :show="isLoading" size="large">
      <NEmpty
        v-if="!isLoading && results.length === 0 && searchQuery"
        description="未找到匹配的诗词"
      >
        <template #extra>
          <NButton @click="clearFilters">
            清除筛选
          </NButton>
        </template>
      </NEmpty>

      <NEmpty
        v-if="!isLoading && results.length === 0 && !searchQuery"
        description="请输入关键词或选择筛选条件"
      >
        <template #extra>
          <NText depth="3" style="font-size: 12px">
            支持按标题、作者名搜索，也可按朝代和体裁筛选
          </NText>
        </template>
      </NEmpty>

      <div v-if="results.length > 0" class="results-container">
        <div class="results-list">
          <article
            v-for="poem in results"
            :key="poem.id"
            class="result-item"
            @click="goToPoem(poem.id)"
          >
            <div class="result-main">
              <NTag :bordered="false" size="small" type="info">
                {{ poem.dynasty || '未知' }}
              </NTag>
              <div class="poem-info">
                <h3 class="poem-title">{{ poem.title || '无题' }}</h3>
                <div class="poem-subtitle">
                  <span class="author">
                    <PersonOutline style="width: 14px; height: 14px; margin-right: 2px" />
                    {{ poem.author }}
                  </span>
                </div>
              </div>
              <ChevronForwardOutline class="arrow-icon" />
            </div>
          </article>
        </div>

        <div class="pagination-wrapper">
          <NPagination
            :page="page"
            :page-count="Math.ceil(totalCount / pageSize)"
            :page-sizes="[12, 24, 48, 96]"
            :page-size="pageSize"
            show-size-picker
            show-quick-jumper
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </div>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.poem-search-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  margin-bottom: 24px;
}

.search-card {
  margin-bottom: 24px;
}

.results-container {
  margin-top: 16px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  background: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.result-item:hover {
  border-color: var(--n-primary-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.poem-info {
  flex: 1;
  min-width: 0;
}

.poem-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color-1);
  margin: 0 0 4px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.poem-subtitle {
  font-size: 13px;
  color: var(--n-text-color-3);
  display: flex;
  align-items: center;
  gap: 8px;
}

.author {
  display: flex;
  align-items: center;
}

.arrow-icon {
  width: 20px;
  height: 20px;
  color: var(--n-text-color-3);
  flex-shrink: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
