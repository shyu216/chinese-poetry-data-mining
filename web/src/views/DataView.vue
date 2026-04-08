<!--
  文件: web/src/views/DataView.vue
  说明: 数据管理一站式页面，整合数据概览、下载与缓存管理功能。
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NCard, NGrid, NGridItem, NStatistic, NButton,
  NSpace, NTag, NProgress, NEmpty, NSpin,
  NNumberAnimation, NDivider, NAlert, NIcon, NResult
} from 'naive-ui'
import {
  CloudDownloadOutline, TrashOutline, SpeedometerOutline,
  CheckmarkOutline, CloseOutline, RefreshOutline, DownloadOutline
} from '@vicons/ionicons5'

import {
  usePoemsMetadata, useAuthorsMetadata, useWordcountMetadata, usePoemIndexManifest,
  POEMS_STORAGE, AUTHORS_STORAGE, WORDCOUNT_STORAGE, POEM_INDEX_STORAGE
} from '@/composables/useMetadataLoader'
import { useKeywordIndex } from '@/composables/useKeywordIndex'
import { useSearchIndex } from '@/composables/useSearchIndex'
import { getMetadata, getCache, clearStorage } from '@/composables/useCache'
import type { PoemsIndex, AuthorsIndex, WordCountMeta } from '@/composables/types'
import { useChunkLoader } from '@/composables/useChunkLoader'
import { usePoems } from '@/composables/usePoems'
import { useAuthors } from '@/composables/useAuthors'
import { useWordcount } from '@/composables/useWordcount'
import type { PoemSummary, AuthorStats, WordCountItem } from '@/composables/types'
import DataItemCard from '@/components/data/DataItemCard.vue'
import { PageHeader } from '@/components/layout'

const chunkLoader = useChunkLoader()
const poems = usePoems()
const authors = useAuthors()
const wordcount = useWordcount()
const searchIndex = useSearchIndex()
const keywordIndex = useKeywordIndex()

const poemsMeta = usePoemsMetadata()
const authorsMeta = useAuthorsMetadata()
const wordcountMeta = useWordcountMetadata()
const poemIndexMeta = usePoemIndexManifest()

const isLoading = ref(false)
const isClearing = ref(false)
const loadError = ref<string | null>(null)

const poemsIndexData = ref<PoemsIndex | null>(null)
const authorsIndexData = ref<AuthorsIndex | null>(null)
const wordcountIndexData = ref<WordCountMeta | null>(null)

const poemStats = ref({
  cachedChunkIds: [] as number[],
  totalChunks: 0,
  loaded: false,
  isDownloading: false
})

const authorStats = ref({
  cachedChunkIds: [] as number[],
  totalChunks: 0,
  loaded: false,
  isDownloading: false
})

const wordcountStats = ref({
  cachedChunkIds: [] as number[],
  totalChunks: 0,
  loaded: false,
  isDownloading: false
})

const searchIndexStats = ref({
  cachedPrefixes: [] as string[],
  totalPrefixes: 0,
  loaded: false,
  isDownloading: false
})

const keywordIndexStats = ref({
  cachedChunks: [] as number[],
  totalChunks: 0,
  loaded: false,
  isDownloading: false
})

const loadStats = async () => {
  isLoading.value = true
  loadError.value = null

  try {
    const poemsMetaData = await poemsMeta.loadMetadata()
    poemsIndexData.value = poemsMetaData
    poemStats.value.totalChunks = poemsMetaData?.metadata?.chunks || 0

    const poemMeta = await getMetadata(POEMS_STORAGE)
    if (poemMeta) {
      poemStats.value.cachedChunkIds = poemMeta.loadedChunkIds || []
      poemStats.value.loaded = true
    }

    const authorsMetaData = await authorsMeta.loadMetadata()
    authorsIndexData.value = authorsMetaData
    authorStats.value.totalChunks = authorsMetaData?.total || 0

    const authorMeta = await getMetadata(AUTHORS_STORAGE)
    if (authorMeta) {
      authorStats.value.cachedChunkIds = authorMeta.loadedChunkIds || []
      authorStats.value.loaded = true
    }

    const wordcountMetaData = await wordcountMeta.loadMetadata()
    wordcountIndexData.value = wordcountMetaData
    wordcountStats.value.totalChunks = wordcountMetaData?.total_chunks || 0

    const wordcountMetaStored = await getMetadata(WORDCOUNT_STORAGE)
    if (wordcountMetaStored) {
      wordcountStats.value.cachedChunkIds = wordcountMetaStored.loadedChunkIds || []
      wordcountStats.value.loaded = true
    }

    const searchIndexMetaData = await poemIndexMeta.loadMetadata()
    const prefixes = Object.keys(searchIndexMetaData?.prefixMap || {})
    searchIndexStats.value.totalPrefixes = prefixes.length

    const searchIndexPrefixes = await getCache<string[]>(POEM_INDEX_STORAGE, 'loaded-prefixes')
    if (searchIndexPrefixes) {
      searchIndexStats.value.cachedPrefixes = searchIndexPrefixes
      searchIndexStats.value.loaded = true
    }

    keywordIndexStats.value.totalChunks = keywordIndex.totalChunks.value
    keywordIndexStats.value.cachedChunks = [...keywordIndex.loadedChunkIds.value]
    keywordIndexStats.value.loaded = keywordIndexStats.value.cachedChunks.length > 0
  } catch (error) {
    console.error('Failed to load stats:', error)
    loadError.value = error instanceof Error ? error.message : '加载数据失败，请刷新页面重试'
  } finally {
    isLoading.value = false
  }
}

const downloadPoems = async () => {
  if (poemStats.value.isDownloading) {
    chunkLoader.stop()
    poemStats.value.isDownloading = false
    return
  }

  const total = poemStats.value.totalChunks
  const allChunkIds = Array.from({ length: total }, (_, i) => i)
  const unloadedChunkIds = allChunkIds.filter(id => !poemStats.value.cachedChunkIds.includes(id))

  if (unloadedChunkIds.length === 0) {
    return
  }

  poemStats.value.isDownloading = true

  await chunkLoader.loadChunks<PoemSummary[]>(unloadedChunkIds, poems.loadChunkSummaries, {
    chunkDelay: 50,
    onChunkLoaded: (chunkId) => {
      if (!poemStats.value.cachedChunkIds.includes(chunkId)) {
        poemStats.value.cachedChunkIds.push(chunkId)
      }
    },
    onComplete: () => {
      poemStats.value.isDownloading = false
    }
  })

  chunkLoader.resume()
}

const downloadAuthors = async () => {
  if (authorStats.value.isDownloading) {
    chunkLoader.stop()
    authorStats.value.isDownloading = false
    return
  }

  const total = authorStats.value.totalChunks
  const allChunkIds = Array.from({ length: total }, (_, i) => i)
  const unloadedChunkIds = allChunkIds.filter(id => !authorStats.value.cachedChunkIds.includes(id))

  if (unloadedChunkIds.length === 0) {
    return
  }

  authorStats.value.isDownloading = true

  await chunkLoader.loadChunks<AuthorStats[]>(unloadedChunkIds, authors.loadAuthorChunk, {
    chunkDelay: 50,
    onChunkLoaded: (chunkId) => {
      if (!authorStats.value.cachedChunkIds.includes(chunkId)) {
        authorStats.value.cachedChunkIds.push(chunkId)
      }
    },
    onComplete: () => {
      authorStats.value.isDownloading = false
    }
  })

  chunkLoader.resume()
}

const downloadWordcount = async () => {
  if (wordcountStats.value.isDownloading) {
    chunkLoader.stop()
    wordcountStats.value.isDownloading = false
    return
  }

  const total = wordcountStats.value.totalChunks
  const allChunkIds = Array.from({ length: total }, (_, i) => i)
  const unloadedChunkIds = allChunkIds.filter(id => !wordcountStats.value.cachedChunkIds.includes(id))

  if (unloadedChunkIds.length === 0) {
    return
  }

  wordcountStats.value.isDownloading = true

  await chunkLoader.loadChunks<WordCountItem[]>(unloadedChunkIds, wordcount.loadChunk, {
    chunkDelay: 50,
    onChunkLoaded: (chunkId) => {
      if (!wordcountStats.value.cachedChunkIds.includes(chunkId)) {
        wordcountStats.value.cachedChunkIds.push(chunkId)
      }
    },
    onComplete: () => {
      wordcountStats.value.isDownloading = false
    }
  })

  chunkLoader.resume()
}

const downloadSearchIndex = async () => {
  if (searchIndexStats.value.isDownloading) {
    chunkLoader.stop()
    searchIndexStats.value.isDownloading = false
    return
  }

  const manifest = await poemIndexMeta.loadMetadata()
  const prefixes = Object.keys(manifest?.prefixMap || {})
  searchIndexStats.value.totalPrefixes = prefixes.length

  const unloadedPrefixes = prefixes.filter(p => !searchIndexStats.value.cachedPrefixes.includes(p))

  if (unloadedPrefixes.length === 0) {
    return
  }

  searchIndexStats.value.isDownloading = true

  const prefixToIndex = new Map(prefixes.map((p, i) => [p, i]))
  const unloadedIndices = unloadedPrefixes.map(p => prefixToIndex.get(p)!).filter((i): i is number => i !== undefined)

  await chunkLoader.loadChunks<string>(unloadedIndices, async (index: number) => {
    const prefix = prefixes[index]!
    await searchIndex.loadPoemChunk(prefix)
    return prefix
  }, {
    chunkDelay: 50,
    onChunkLoaded: (_, prefix) => {
      const prefixStr = String(prefix)
      if (!searchIndexStats.value.cachedPrefixes.includes(prefixStr)) {
        searchIndexStats.value.cachedPrefixes.push(prefixStr)
      }
    },
    onComplete: () => {
      searchIndexStats.value.isDownloading = false
    }
  })

  chunkLoader.resume()
}

const downloadKeywordIndex = async () => {
  if (keywordIndexStats.value.isDownloading) {
    chunkLoader.stop()
    keywordIndexStats.value.isDownloading = false
    return
  }

  await keywordIndex.searchKeywordOptimized('')
  keywordIndexStats.value.totalChunks = keywordIndex.totalChunks.value

  const unloadedChunks = []
  for (let i = 0; i < keywordIndexStats.value.totalChunks; i++) {
    if (!keywordIndexStats.value.cachedChunks.includes(i)) {
      unloadedChunks.push(i)
    }
  }

  if (unloadedChunks.length === 0) {
    return
  }

  keywordIndexStats.value.isDownloading = true

  await chunkLoader.loadChunks<number>(unloadedChunks, async (index: number) => {
    await keywordIndex.loadChunk(index)
    return index
  }, {
    chunkDelay: 30,
    onChunkLoaded: (index) => {
      const idx = index as number
      if (!keywordIndexStats.value.cachedChunks.includes(idx)) {
        keywordIndexStats.value.cachedChunks.push(idx)
      }
    },
    onComplete: () => {
      keywordIndexStats.value.isDownloading = false
    }
  })

  chunkLoader.resume()
}

const handleClearCache = async () => {
  isClearing.value = true

  await Promise.all([
    clearStorage(POEMS_STORAGE),
    clearStorage(AUTHORS_STORAGE),
    clearStorage(WORDCOUNT_STORAGE),
    clearStorage(POEM_INDEX_STORAGE),
    clearStorage(keywordIndex.storageName)
  ])

  poemStats.value.cachedChunkIds = []
  authorStats.value.cachedChunkIds = []
  wordcountStats.value.cachedChunkIds = []
  searchIndexStats.value.cachedPrefixes = []
  keywordIndexStats.value.cachedChunks = []

  isClearing.value = false
  await loadStats()
}

const poemChunkBars = computed(() => {
  if (!poemsIndexData.value?.chunks) return []
  const cachedSet = new Set(poemStats.value.cachedChunkIds)
  return poemsIndexData.value.chunks.map((chunk: { id: number; count: number }) => ({
    id: chunk.id,
    count: chunk.count,
    cached: cachedSet.has(chunk.id)
  }))
})

const authorChunkBars = computed(() => {
  if (!authorsIndexData.value?.chunks) return []
  const cachedSet = new Set(authorStats.value.cachedChunkIds)
  return authorsIndexData.value.chunks.map((chunk: { index: number; authorCount: number }) => ({
    id: chunk.index,
    count: chunk.authorCount,
    cached: cachedSet.has(chunk.index)
  }))
})

const wordcountChunkBars = computed(() => {
  if (!wordcountIndexData.value?.chunks) return []
  const cachedSet = new Set(wordcountStats.value.cachedChunkIds)
  return wordcountIndexData.value.chunks.map((chunk: { index: number; count: number }) => ({
    id: chunk.index,
    count: chunk.count,
    cached: cachedSet.has(chunk.index)
  }))
})

const maxPoemCount = computed(() => {
  if (!poemChunkBars.value.length) return 0
  return Math.max(...poemChunkBars.value.map((c: { count: number }) => c.count), 1)
})

const maxAuthorCount = computed(() => {
  if (!authorChunkBars.value.length) return 0
  return Math.max(...authorChunkBars.value.map((c: { count: number }) => c.count), 1)
})

const maxWordcountCount = computed(() => {
  if (!wordcountChunkBars.value.length) return 0
  return Math.max(...wordcountChunkBars.value.map((c: { count: number }) => c.count), 1)
})

const searchIndexChunkBars = computed(() => {
  const total = searchIndexStats.value.totalPrefixes
  if (total === 0) return []
  const cachedSet = new Set(searchIndexStats.value.cachedPrefixes)
  const prefixCount = Math.ceil(total / 50)
  return Array.from({ length: total }, (_, i) => ({
    id: i,
    count: prefixCount,
    cached: cachedSet.has(String(i))
  }))
})

const keywordIndexChunkBars = computed(() => {
  const total = keywordIndexStats.value.totalChunks
  if (total === 0) return []
  const cachedSet = new Set(keywordIndexStats.value.cachedChunks)
  return Array.from({ length: total }, (_, i) => ({
    id: i,
    count: 1,
    cached: cachedSet.has(i)
  }))
})

const downloadProgress = computed(() => {
  const total = poemStats.value.totalChunks + authorStats.value.totalChunks + wordcountStats.value.totalChunks
  const cached = poemStats.value.cachedChunkIds.length + authorStats.value.cachedChunkIds.length + wordcountStats.value.cachedChunkIds.length
  return total > 0 ? Math.round((cached / total) * 100) : 0
})

const poemIsFullyDownloaded = computed(() => {
  return poemStats.value.cachedChunkIds.length === poemStats.value.totalChunks &&
         poemStats.value.totalChunks > 0
})

const authorIsFullyDownloaded = computed(() => {
  return authorStats.value.cachedChunkIds.length === authorStats.value.totalChunks &&
         authorStats.value.totalChunks > 0
})

const wordcountIsFullyDownloaded = computed(() => {
  return wordcountStats.value.cachedChunkIds.length === wordcountStats.value.totalChunks &&
         wordcountStats.value.totalChunks > 0
})

const searchIndexIsFullyDownloaded = computed(() => {
  return searchIndexStats.value.cachedPrefixes.length === searchIndexStats.value.totalPrefixes &&
         searchIndexStats.value.totalPrefixes > 0
})

const keywordIndexIsFullyDownloaded = computed(() => {
  return keywordIndexStats.value.cachedChunks.length === keywordIndexStats.value.totalChunks &&
         keywordIndexStats.value.totalChunks > 0
})

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="data-view">
    <PageHeader
      title="数据管理"
      subtitle="一站式管理本地缓存数据，支持离线浏览与下载"
      :icon="CloudDownloadOutline"
    />

    <NCard v-if="isLoading" class="loading-card">
      <NSpin size="large" />
    </NCard>

    <NCard v-else-if="loadError" class="error-card">
      <NResult
        status="error"
        title="加载失败"
        :description="loadError"
      >
        <template #footer>
          <NButton type="primary" @click="loadStats">
            <template #icon>
              <NIcon :component="RefreshOutline" />
            </template>
            重新加载
          </NButton>
        </template>
      </NResult>
    </NCard>

    <template v-else-if="!loadError">
      <NAlert type="info" :show-icon="false" style="margin-bottom: 16px;">
        当前已缓存 {{ downloadProgress }}% 的数据，部分数据需要下载后才能离线浏览。
      </NAlert>

      <NGrid :cols="2" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <NGridItem span="2 m:1">
          <DataItemCard
            icon="📚"
            title="诗词数据"
            :description="`共 ${poemStats.totalChunks} 个分块，${poemStats.cachedChunkIds.length} 个已缓存`"
            :cached-count="poemStats.cachedChunkIds.length"
            :total-count="poemStats.totalChunks"
            :bars="poemChunkBars"
            :max-count="maxPoemCount"
            color-class="poems"
          >
            <template #action>
              <NButton
                :type="poemStats.isDownloading ? 'error' : (poemIsFullyDownloaded ? 'default' : 'primary')"
                size="small"
                :disabled="poemIsFullyDownloaded && !poemStats.isDownloading"
                @click="downloadPoems"
              >
                <template #icon>
                  <NIcon :component="poemStats.isDownloading ? CloseOutline : DownloadOutline" />
                </template>
                {{ poemStats.isDownloading ? '取消' : (poemIsFullyDownloaded ? '已下载' : '下载') }}
              </NButton>
            </template>
          </DataItemCard>
        </NGridItem>

        <NGridItem span="2 m:1">
          <DataItemCard
            icon="👤"
            title="作者数据"
            :description="`共 ${authorStats.totalChunks} 个分块，${authorStats.cachedChunkIds.length} 个已缓存`"
            :cached-count="authorStats.cachedChunkIds.length"
            :total-count="authorStats.totalChunks"
            :bars="authorChunkBars"
            :max-count="maxAuthorCount"
            color-class="authors"
          >
            <template #action>
              <NButton
                :type="authorStats.isDownloading ? 'error' : (authorIsFullyDownloaded ? 'default' : 'primary')"
                size="small"
                :disabled="authorIsFullyDownloaded && !authorStats.isDownloading"
                @click="downloadAuthors"
              >
                <template #icon>
                  <NIcon :component="authorStats.isDownloading ? CloseOutline : DownloadOutline" />
                </template>
                {{ authorStats.isDownloading ? '取消' : (authorIsFullyDownloaded ? '已下载' : '下载') }}
              </NButton>
            </template>
          </DataItemCard>
        </NGridItem>

        <NGridItem span="2 m:1">
          <DataItemCard
            icon="📊"
            title="分词数据"
            :description="`共 ${wordcountStats.totalChunks} 个分块，${wordcountStats.cachedChunkIds.length} 个已缓存`"
            :cached-count="wordcountStats.cachedChunkIds.length"
            :total-count="wordcountStats.totalChunks"
            :bars="wordcountChunkBars"
            :max-count="maxWordcountCount"
            color-class="wordcount"
          >
            <template #action>
              <NButton
                :type="wordcountStats.isDownloading ? 'error' : (wordcountIsFullyDownloaded ? 'default' : 'primary')"
                size="small"
                :disabled="wordcountIsFullyDownloaded && !wordcountStats.isDownloading"
                @click="downloadWordcount"
              >
                <template #icon>
                  <NIcon :component="wordcountStats.isDownloading ? CloseOutline : DownloadOutline" />
                </template>
                {{ wordcountStats.isDownloading ? '取消' : (wordcountIsFullyDownloaded ? '已下载' : '下载') }}
              </NButton>
            </template>
          </DataItemCard>
        </NGridItem>

        <NGridItem span="2 m:1">
          <DataItemCard
            icon="🔍"
            title="诗词ID索引"
            :description="`共 ${searchIndexStats.totalPrefixes} 个前缀，${searchIndexStats.cachedPrefixes.length} 个已缓存`"
            :cached-count="searchIndexStats.cachedPrefixes.length"
            :total-count="searchIndexStats.totalPrefixes"
            :bars="searchIndexChunkBars"
            :max-count="searchIndexStats.totalPrefixes"
            color-class="searchindex"
          >
            <template #action>
              <NButton
                :type="searchIndexStats.isDownloading ? 'error' : (searchIndexIsFullyDownloaded ? 'default' : 'primary')"
                size="small"
                :disabled="searchIndexIsFullyDownloaded && !searchIndexStats.isDownloading"
                @click="downloadSearchIndex"
              >
                <template #icon>
                  <NIcon :component="searchIndexStats.isDownloading ? CloseOutline : DownloadOutline" />
                </template>
                {{ searchIndexStats.isDownloading ? '取消' : (searchIndexIsFullyDownloaded ? '已下载' : '下载') }}
              </NButton>
            </template>
          </DataItemCard>
        </NGridItem>

        <NGridItem span="2 m:1">
          <DataItemCard
            icon="🏷️"
            title="分词索引"
            :description="`共 ${keywordIndexStats.totalChunks} 个分块，${keywordIndexStats.cachedChunks.length} 个已缓存`"
            :cached-count="keywordIndexStats.cachedChunks.length"
            :total-count="keywordIndexStats.totalChunks"
            :bars="keywordIndexChunkBars"
            :max-count="keywordIndexStats.totalChunks"
            color-class="keywordindex"
          >
            <template #action>
              <NButton
                :type="keywordIndexStats.isDownloading ? 'error' : (keywordIndexIsFullyDownloaded ? 'default' : 'primary')"
                size="small"
                :disabled="keywordIndexIsFullyDownloaded && !keywordIndexStats.isDownloading"
                @click="downloadKeywordIndex"
              >
                <template #icon>
                  <NIcon :component="keywordIndexStats.isDownloading ? CloseOutline : DownloadOutline" />
                </template>
                {{ keywordIndexStats.isDownloading ? '取消' : (keywordIndexIsFullyDownloaded ? '已下载' : '下载') }}
              </NButton>
            </template>
          </DataItemCard>
        </NGridItem>
      </NGrid>

      <NDivider />

      <div class="action-bar">
        <NButton
          type="error"
          size="large"
          :loading="isClearing"
          @click="handleClearCache"
        >
          <template #icon>
            <TrashOutline />
          </template>
          清除所有缓存
        </NButton>
      </div>
    </template>
  </div>
</template>

<style scoped>
.data-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.loading-card {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.error-card {
  margin-bottom: 16px;
}

.action-bar {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}
</style>
