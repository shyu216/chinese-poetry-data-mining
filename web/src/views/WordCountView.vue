<!--
  文件: web/src/views/WordCountView.vue
  说明: 词频页面，展示词频统计、词云与相似词功能；使用按块加载（chunked loading）与本地缓存（IndexedDB）来处理大规模词表数据。

  数据管线:
    - 元数据: 通过 `useWordcountMetadata` / `useWordSimilarityMetadata` 获取索引与分片信息。
    - 分块加载: 使用 `useChunkLoader` 按需请求 chunk（分片），并将已下载分片缓存在 IndexedDB/Cache（`getCache` / `getVerifiedChunkedCache`）。
    - 搜索/相似度: `useWordSearch` 提供快速检索，`useWordSimilarityV2` 提供相似词数据，二者配合按需加载词表分片。

  复杂度:
    - 单次页面展示/搜索主要受已加载项 k 影响，为 O(k)；全量扫描或聚合会随已加载词数增长为 O(n)。
    - 分片数量 t 决定网络与 I/O 成本，总体空间为 O(n)（所有 chunk 累计）。

  使用技术/要点:
    - 按块（chunk）分发与本地缓存减少首屏与内存压力，同时允许渐进加载较大数据集。
    - 组合式 composables 将元数据、缓存和 chunk loader 解耦，便于测试与复用。

  潜在问题/改进建议:
    - Chunk 解析/JSON.parse 在主线程可能阻塞，建议将解析移到 Web Worker。
    - 并发下载过多 chunk 会造成网络拥塞，应限制并发数并实现断点续传/重试。
    - 索引搜索若依赖全量内存索引会占用大量内存，建议采用磁盘索引或倒排索引分片加载策略。
    - UI 未明显使用虚拟列表，长列表渲染可能造成 DOM 性能问题。
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch, shallowRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NCard, NEmpty, NInput, NSpace, NTag,
  NButton, NPagination, NGrid, NGridItem, NProgress, NSelect
} from 'naive-ui'
import {
  TextOutline,
  LibraryOutline, StarOutline, ResizeOutline, GitNetworkOutline
} from '@vicons/ionicons5'
import { useWordcountV2 } from '@/composables/useWordcountV2'
import { useWordSimilarityV2 } from '@/composables/useWordSimilarityV2'
import { useChunkLoader, CHUNK_LOADER_PREFERENCE_KEYS } from '@/composables/useChunkLoader'
import { useWordcountMetadata, WORDCOUNT_STORAGE } from '@/composables/useMetadataLoader'
import { useWordSimilarityMetadata, WORD_SIMILARITY_STORAGE } from '@/composables/useMetadataLoader'
import { getMetadata, getCache, getVerifiedChunkedCache } from '@/composables/useCacheV2'
import { useWordSearch } from '@/search'
import type { WordCountItem } from '@/composables/types'
import { PageHeader, FilterSection } from '@/components/layout'
import { StatsCard, WordCloud } from '@/components/display'
import { ChunkLoaderStatus } from '@/components/feedback'
import { SearchContainer } from '@/components/search'
import { useLoading } from '@/composables/useLoading'

const loading = useLoading()
const wordcountV2 = useWordcountV2()
const wordSimV2 = useWordSimilarityV2()
const router = useRouter()
const route = useRoute()
const wordcountMeta = useWordcountMetadata()
const wordSimMeta = useWordSimilarityMetadata()
const chunkLoader = useChunkLoader({ preferenceKey: CHUNK_LOADER_PREFERENCE_KEYS.wordcount })
const wordSimChunkLoader = useChunkLoader({
  preferenceKey: CHUNK_LOADER_PREFERENCE_KEYS.wordcountWordSim
})

// 新的词汇搜索模块
const { search: searchWords, isReady: wordSearchReady } = useWordSearch()
const isSearching = ref(false)
const searchStats = ref({ queryTime: 0, source: '' })

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const loadedWords = shallowRef<WordCountItem[]>([])
const hasMoreChunks = ref(true)
const isInitializing = ref(true)
const cachedChunksCount = ref(0)
const totalWords = ref(0)
const totalChunks = ref(0)
const lengthFilter = ref<string | null>(null)
const wordCloudTitle = ref('')

// 词频相似度模块数据
interface WordSimItem {
  word: string
  wordId: number
  frequency: number
  loaded: boolean
  similarWords: Array<{ word: string; similarity: number }>
}

const loadedWordSimWords = shallowRef<WordSimItem[]>([])
const wordSimCachedChunksCount = ref(0)
const wordSimTotalChunks = ref(0)
const isWordSimInitializing = ref(true)
const wordSimHasMoreChunks = ref(true)

const lengthOptions = [
  { label: '全部长度', value: '' },
  { label: '单字', value: '1' },
  { label: '二字', value: '2' },
  { label: '三字', value: '3' },
  { label: '四字', value: '4' },
  { label: '五字及以上', value: '5+' }
]

// 搜索结果
const searchResults = ref<WordCountItem[]>([])
const searchTotal = ref(0)

const filteredWords = computed(() => {
  let result = loadedWords.value

  if (lengthFilter.value) {
    if (lengthFilter.value === '5+') {
      result = result.filter(w => w.word.length >= 5)
    } else {
      const len = parseInt(lengthFilter.value)
      result = result.filter(w => w.word.length === len)
    }
  }

  if (!searchQuery.value.trim()) {
    return result
  }
  const query = searchQuery.value.toLowerCase()
  return result.filter(w =>
    w.word.toLowerCase().includes(query)
  )
})

// 使用 WordSearch 搜索
const performSearch = async () => {
  const query = searchQuery.value.trim()
  if (!query || !wordSearchReady.value) {
    searchResults.value = []
    searchTotal.value = 0
    return
  }

  isSearching.value = true
  try {
    const result = await searchWords(query, {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
    searchResults.value = result.items
    searchTotal.value = result.total
    searchStats.value = { queryTime: result.queryTime, source: result.source }
  } finally {
    isSearching.value = false
  }
}

const displayWords = computed(() => {
  const query = searchQuery.value.trim()
  if (query && wordSearchReady.value) {
    return searchResults.value
  }
  return filteredWords.value
})

// 显示的总数（用于搜索统计）
const displayTotal = computed(() => {
  const query = searchQuery.value.trim()
  if (query && wordSearchReady.value) {
    return searchTotal.value
  }
  return filteredWords.value.length
})

const totalPages = computed(() => {
  const query = searchQuery.value.trim()
  if (query && wordSearchReady.value) {
    return Math.ceil(searchTotal.value / pageSize.value)
  }
  return Math.ceil(displayWords.value.length / pageSize.value)
})

const paginatedWords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return displayWords.value.slice(start, end)
})

// 合并后的统计计算属性
const globalTotalWords = computed(() => wordcountV2.totalWords.value || 0)
const globalTotalChunks = computed(() => wordcountV2.totalChunks.value || 0)

const topCount = computed(() => {
  if (loadedWords.value.length === 0) return 0
  return loadedWords.value[0]?.count || 0
})

const avgWordLength = computed(() => {
  if (loadedWords.value.length === 0) return '-'
  const totalWeightedLength = loadedWords.value.reduce(
    (sum, w) => sum + (w.word?.length || 0) * (w.count || 0), 0
  )
  const totalCount = loadedWords.value.reduce(
    (sum, w) => sum + (w.count || 0), 0
  )
  return totalCount > 0 ? (totalWeightedLength / totalCount).toFixed(2) : '0'
})

const loadedChunksCount = computed(() => cachedChunksCount.value + chunkLoader.loadedCount.value)
const hasMoreToLoad = computed(() => loadedChunksCount.value < totalChunks.value)

const loadingHint = computed(() => {
  const count = loadedWords.value.length
  if (count === 0) return '正在连接...'
  return `已加载 ${count.toLocaleString()} 个词汇`
})

const loadCachedChunks = async (): Promise<number[]> => {
  console.log('[WordCountView] 🔄 开始加载本地缓存...')
  const startTime = performance.now()

  const meta = await getMetadata(WORDCOUNT_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  cachedChunksCount.value = loadedChunkIds.length
  console.log(`[WordCountView] 📦 发现 ${loadedChunkIds.length} 个缓存分块`)

  if (loadedChunkIds.length === 0) {
    console.log('[WordCountView] ⚠️ 无缓存数据，将从服务器加载')
    return []
  }

  const cachedWords: WordCountItem[] = []
  console.log(`[WordCountView] 📖 开始读取 ${loadedChunkIds.length} 个缓存分块...`)
  for (const chunkId of loadedChunkIds) {
    const chunkStartTime = performance.now()
    const chunkData = await getVerifiedChunkedCache<WordCountItem[]>(WORDCOUNT_STORAGE, chunkId)
    const chunkDuration = Math.round(performance.now() - chunkStartTime)

    if (chunkData && Array.isArray(chunkData)) {
      // 转换数组格式 [word, count, rank] 为对象格式 {word, count, rank}
      const convertedData = chunkData.map((item: any) => {
        if (Array.isArray(item)) {
          return { word: item[0], count: item[1], rank: item[2] }
        }
        return item as WordCountItem
      })
      cachedWords.push(...convertedData)
      console.log(`[WordCountView]   ├─ 分块 #${chunkId}: ${chunkData.length} 个词汇 (${chunkDuration}ms)`)
    }
  }

  if (cachedWords.length > 0) {
    loadedWords.value = cachedWords.sort((a, b) => a.rank - b.rank)
    totalWords.value = cachedWords.length

    // Debug: 检查缓存数据
    console.log('[loadCachedChunks] 加载完成:', {
      total: cachedWords.length,
      sample: cachedWords.slice(0, 3)
    })
  }

  const totalDuration = Math.round(performance.now() - startTime)
  console.log(`[WordCountView] ✅ 缓存加载完成: ${cachedWords.length} 个词汇 - ${totalDuration}ms`)

  return loadedChunkIds
}

const loadData = async () => {
  console.log('[WordCountView] 🚀 开始加载数据...')
  const totalStartTime = performance.now()

  // 步骤 1: 初始化 - 开始 blocking loading
  loading.startBlocking('词频统计', '正在加载词频数据...')
  isInitializing.value = true

  try {
    loading.updatePhase('metadata', '正在加载元数据...')
    loading.updateProgress(0, 4)
    console.log('[WordCountView] 📋 阶段1: 加载元数据...')
    const metaStartTime = performance.now()
    await wordcountMeta.loadMetadata()
    const totalChunksCount = globalTotalChunks.value || 0
    totalChunks.value = totalChunksCount
    console.log(`[WordCountView] ✅ 元数据加载完成: ${globalTotalWords.value} 个词汇, ${totalChunksCount} 个分块 - ${Math.round(performance.now() - metaStartTime)}ms`)

    loading.updateProgress(1, 4, '正在检查本地缓存...')
    console.log('[WordCountView] 💾 阶段2: 检查本地缓存...')
    const cacheStartTime = performance.now()
    const loadedChunkIds = await loadCachedChunks()
    console.log(`[WordCountView] ✅ 缓存检查完成 - ${Math.round(performance.now() - cacheStartTime)}ms`)

    loading.updateProgress(2, 4, '正在准备词频展示...')
    console.log('[WordCountView] 🎨 阶段3: 准备UI...')
    const uiStartTime = performance.now()

    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))
    console.log(`[WordCountView] 📊 需要加载的分块: ${unloadedChunkIds.length} 个 (已缓存: ${loadedChunkIds.length} 个)`)
    console.log(`[WordCountView] ✅ UI准备完成 - ${Math.round(performance.now() - uiStartTime)}ms`)

    loading.updateProgress(3, 4, '准备就绪...')
    loading.updatePhase('complete', '数据加载完成')
    loading.updateProgress(4, 4)
    setTimeout(() => loading.finish(), 300)

    if (unloadedChunkIds.length === 0) {
      console.log('[WordCountView] ✨ 所有数据已从缓存加载，无需网络请求')
      hasMoreChunks.value = false
      isInitializing.value = false
      return
    }

    console.log('[WordCountView] 🌐 阶段4: 开始后台加载网络数据...')
    const bgStartTime = performance.now()
    if (chunkLoader.autoLoadEnabled.value) {
      loading.startNonBlocking('补充词频数据', '正在加载剩余数据...')
    } else {
      console.log(
        '[WordCountView] autoLoadOnEnter=false (wordcount) — skip unified non-blocking toast; chunk load may be paused'
      )
    }

    let currentLoadedCount = loadedChunkIds.length
    let networkDataCount = 0

    // 使用批量收集，减少排序次数
    const batchWords: WordCountItem[] = []
    let lastSortTime = Date.now()

    const runWordcountNetworkLoad = () =>
      chunkLoader.loadChunks<WordCountItem[]>(unloadedChunkIds, wordcountV2.loadChunk, {
        concurrency: 5,
        chunkDelay: 0,
        onChunkLoaded: (_, words) => {
          const wordsArray = words as WordCountItem[]
          batchWords.push(...wordsArray)
          networkDataCount += wordsArray.length

          currentLoadedCount++
          const progress = Math.round((currentLoadedCount / totalChunksCount) * 100)

          // 每2秒或每10%更新一次UI，避免频繁排序
          const now = Date.now()
          const shouldUpdateUI = now - lastSortTime > 2000 ||
            currentLoadedCount % Math.max(1, Math.floor(totalChunksCount / 10)) === 0

          if (shouldUpdateUI) {
            loadedWords.value = [...loadedWords.value, ...batchWords].sort((a, b) => a.rank - b.rank)
            totalWords.value = loadedWords.value.length
            batchWords.length = 0  // 清空批量缓冲区
            lastSortTime = now
          }

          // 每加载10%更新一次提示
          if (currentLoadedCount % Math.max(1, Math.floor(totalChunksCount / 10)) === 0) {
            const phases = ['正在读取词频数据...', '正在整理词汇数据...', '正在加载词频信息...', '正在构建词频列表...']
            const phase = phases[Math.floor((currentLoadedCount / totalChunksCount) * phases.length)] || phases[0]
            loading.updateProgress(currentLoadedCount, totalChunksCount, `${phase} (${currentLoadedCount}/${totalChunksCount})`)
            console.log(`[WordCountView] 📥 后台加载进度: ${progress}% (${currentLoadedCount}/${totalChunksCount} 分块, ${networkDataCount} 个词汇)`)
          }
        },
        onComplete: () => {
          // 确保剩余数据被添加
          if (batchWords.length > 0) {
            loadedWords.value = [...loadedWords.value, ...batchWords].sort((a, b) => a.rank - b.rank)
            totalWords.value = loadedWords.value.length
          }
          const bgDuration = Math.round(performance.now() - bgStartTime)
          console.log(`[WordCountView] ✅ 后台加载完成: ${networkDataCount} 个词汇 - ${bgDuration}ms`)
          hasMoreChunks.value = false
          loading.finish()
        }
      })

    if (chunkLoader.autoLoadEnabled.value) {
      await runWordcountNetworkLoad()
    } else {
      console.log(
        '[WordCountView] autoLoadOnEnter=false (localStorage, wordcount) — network chunk load started paused; not awaiting loadData'
      )
      void runWordcountNetworkLoad()
    }
  } catch (error) {
    loading.error('加载失败，请刷新重试')
    console.error('[WordCountView] ❌ 词频数据加载失败:', error)
  } finally {
    const totalDuration = Math.round(performance.now() - totalStartTime)
    console.log(`[WordCountView] 🏁 总加载时间: ${totalDuration}ms`)
    isInitializing.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handlePageChange = (p: number) => {
  currentPage.value = p
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const clearFilters = () => {
  searchQuery.value = ''
  lengthFilter.value = null
  currentPage.value = 1
}

const goToKeyword = (word: string) => {
  router.push(`/keyword/${encodeURIComponent(word)}`)
}

// 词频相似度模块加载函数
const loadWordSimCachedChunks = async (): Promise<number[]> => {
  console.log('[WordCountView] 🔄 [词频相似度] 开始加载本地缓存...')
  const startTime = performance.now()

  const vocab = await getCache<Record<string, number>>(WORD_SIMILARITY_STORAGE, 'vocab')

  if (!vocab || Object.keys(vocab).length === 0) {
    console.log('[WordCountView] ⚠️ [词频相似度] 无词汇表缓存')
    return []
  }
  console.log(`[WordCountView] 📚 [词频相似度] 词汇表已加载: ${Object.keys(vocab).length} 个词`)

  const meta = await getMetadata(WORD_SIMILARITY_STORAGE)
  const loadedChunkIds = meta?.loadedChunkIds || []

  wordSimCachedChunksCount.value = loadedChunkIds.length
  console.log(`[WordCountView] 📦 [词频相似度] 发现 ${loadedChunkIds.length} 个缓存分块`)

  const vocabReverseMap = wordSimV2.getVocabReverseMap()
  let loadedCount = 0

  for (const chunkId of loadedChunkIds) {
    const chunkStartTime = performance.now()
    const cached = await getVerifiedChunkedCache<{ vocab: string[], entries: [number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }][] }>(WORD_SIMILARITY_STORAGE, chunkId)
    const chunkDuration = Math.round(performance.now() - chunkStartTime)
    const batchWords: typeof loadedWordSimWords.value = []
    if (cached) {
      const entries = new Map(cached.entries)
      for (const [wordId, entry] of entries) {
        const word = vocabReverseMap.get(wordId) || ''
        batchWords.push({
          word,
          wordId,
          frequency: entry.frequency,
          loaded: true,
          similarWords: entry.similarWords.slice(0, 5).map(sw => ({
            word: vocabReverseMap.get(sw.wordId) || '',
            similarity: sw.similarity
          }))
        })
      }
      loadedCount += entries.size
      console.log(`[WordCountView]   ├─ [词频相似度] 分块 #${chunkId}: ${entries.size} 个词 (${chunkDuration}ms)`)
    }
    // 一次性批量添加所有缓存的词频相似度数据
    if (batchWords.length > 0) {
      loadedWordSimWords.value = [...loadedWordSimWords.value, ...batchWords]
    }
  }


  const totalDuration = Math.round(performance.now() - startTime)
  console.log(`[WordCountView] ✅ [词频相似度] 缓存加载完成: ${loadedCount} 个词 - ${totalDuration}ms`)

  return loadedChunkIds
}

const loadWordSimData = async () => {
  console.log('[WordCountView] 🚀 [词频相似度] 开始加载数据...')
  const totalStartTime = performance.now()

  isWordSimInitializing.value = true
  try {
    console.log('[WordCountView] 📋 [词频相似度] 加载元数据...')
    const metaStartTime = performance.now()
    await wordSimMeta.loadMetadata()
    const totalChunksCount = wordSimV2.totalChunks.value || 0
    wordSimTotalChunks.value = totalChunksCount
    console.log(`[WordCountView] ✅ [词频相似度] 元数据加载完成: ${totalChunksCount} 个分块 - ${Math.round(performance.now() - metaStartTime)}ms`)

    console.log('[WordCountView] 📚 [词频相似度] 加载词汇表...')
    const vocabStartTime = performance.now()
    await wordSimV2.loadVocab()
    console.log(`[WordCountView] ✅ [词频相似度] 词汇表加载完成 - ${Math.round(performance.now() - vocabStartTime)}ms`)

    const loadedChunkIds = await loadWordSimCachedChunks()

    const allChunkIds = Array.from({ length: totalChunksCount }, (_, i) => i)
    const unloadedChunkIds = allChunkIds.filter(id => !loadedChunkIds.includes(id))
    console.log(`[WordCountView] 📊 [词频相似度] 需要加载的分块: ${unloadedChunkIds.length} 个 (已缓存: ${loadedChunkIds.length} 个)`)

    if (unloadedChunkIds.length === 0) {
      console.log('[WordCountView] ✨ [词频相似度] 所有数据已从缓存加载，无需网络请求')
      wordSimHasMoreChunks.value = false
      return
    }

    console.log('[WordCountView] 🌐 [词频相似度] 开始后台加载网络数据...')
    const bgStartTime = performance.now()
    let networkDataCount = 0
    let currentLoadedCount = loadedChunkIds.length

    const runWordSimNetworkLoad = () =>
      wordSimChunkLoader.loadChunks(unloadedChunkIds, wordSimV2.loadChunk, {
        chunkDelay: 100,
        onChunkLoaded: (_, chunk: any) => {
          networkDataCount++
          currentLoadedCount++
          const progress = Math.round((currentLoadedCount / totalChunksCount) * 100)

          // 每加载10%更新一次日志
          if (currentLoadedCount % Math.max(1, Math.floor(totalChunksCount / 10)) === 0) {
            console.log(`[WordCountView] 📥 [词频相似度] 后台加载进度: ${progress}% (${currentLoadedCount}/${totalChunksCount} 分块, ${networkDataCount} 个词频相似度)`)
          }

          const vocabReverseMap = wordSimV2.getVocabReverseMap()
          const entries = chunk.entries as Map<number, { frequency: number; similarWords: Array<{ wordId: number; similarity: number }> }>

          // 批量处理，避免频繁触发响应式更新
          const newWords: typeof loadedWordSimWords.value = []
          const existingWordIds = new Set(loadedWordSimWords.value.map(w => w.wordId))

          for (const [wordId, entry] of entries) {
            if (!existingWordIds.has(wordId)) {
              const word = vocabReverseMap.get(wordId) || ''
              newWords.push({
                word,
                wordId,
                frequency: entry.frequency,
                loaded: true,
                similarWords: entry.similarWords.slice(0, 5).map(sw => ({
                  word: vocabReverseMap.get(sw.wordId) || '',
                  similarity: sw.similarity
                }))
              })
            }
          }

          // 一次性批量添加，减少响应式更新次数
          if (newWords.length > 0) {
            loadedWordSimWords.value = [...loadedWordSimWords.value, ...newWords]
          }
        },
        onComplete: () => {
          const bgDuration = Math.round(performance.now() - bgStartTime)
          console.log(`[WordCountView] ✅ [词频相似度] 后台加载完成: ${networkDataCount} 个分块 - ${bgDuration}ms`)
          wordSimHasMoreChunks.value = false
        }
      })

    if (wordSimChunkLoader.autoLoadEnabled.value) {
      await runWordSimNetworkLoad()
    } else {
      console.log(
        '[WordCountView] autoLoadOnEnter=false (localStorage, wordSim) — similarity chunk load started paused; not awaiting loadWordSimData'
      )
      void runWordSimNetworkLoad()
    }
  } finally {
    const totalDuration = Math.round(performance.now() - totalStartTime)
    console.log(`[WordCountView] 🏁 [词频相似度] 总加载时间: ${totalDuration}ms`)
    isWordSimInitializing.value = false
  }
}

// 词频相似度模块计算属性
const wordSimLoadedChunksCount = computed(() => wordSimCachedChunksCount.value + wordSimChunkLoader.loadedCount.value)
const wordSimHasMoreToLoad = computed(() => wordSimLoadedChunksCount.value < wordSimTotalChunks.value)

const wordSimLoadingHint = computed(() => {
  const count = loadedWordSimWords.value.length
  if (count === 0) return '正在连接...'
  return `已加载 ${count.toLocaleString()} 个词汇`
})

// 获取词的词频相似度信息
const getWordSimInfo = (word: string): { status: 'loading' | 'no-data' | 'has-data', similarWords: Array<{ word: string; similarity: number }> } => {
  const simWord = loadedWordSimWords.value.find(w => w.word === word)
  if (!simWord) {
    // 如果词频相似度数据还在加载中，返回loading状态
    if (wordSimChunkLoader.isLoading.value || isWordSimInitializing.value) {
      return { status: 'loading', similarWords: [] }
    }
    return { status: 'no-data', similarWords: [] }
  }
  if (simWord.similarWords.length === 0) {
    return { status: 'no-data', similarWords: [] }
  }
  return { status: 'has-data', similarWords: simWord.similarWords }
}

const getSimilarityColor = (similarity: number) => {
  if (similarity >= 0.9) return 'success'
  if (similarity >= 0.7) return 'warning'
  if (similarity >= 0.5) return 'info'
  return 'default'
}

const getSimilarityPercent = (similarity: number) => {
  return Math.round(similarity * 100)
}

/** 列表卡片用：每个词只算一次相似度信息，避免模板重复调用 */
const paginatedWordCards = computed(() =>
  paginatedWords.value.map((w) => ({
    ...w,
    sim: getWordSimInfo(w.word)
  }))
)

const isLoading = computed(() => (chunkLoader.isLoading.value && loadedWords.value.length === 0))

const wordcloudWords = computed(() => {
  let result = loadedWords.value

  if (lengthFilter.value) {
    if (lengthFilter.value === '5+') {
      result = result.filter(w => w.word.length >= 5)
    } else {
      const len = parseInt(lengthFilter.value)
      result = result.filter(w => w.word.length === len)
    }
  }

  const sel = lengthOptions.find(o => o.value === (lengthFilter.value ?? '')) || lengthOptions[0]
  wordCloudTitle.value = `${sel?.label}高频词云`

  return result.slice(0, 100)
})

const isWordCloudReady = computed(() => loadedWords.value.length > 0 && !chunkLoader.isLoading.value)

const handleWordCloudClick = (word: WordCountItem) => {
  goToKeyword(word.word)
}

onMounted(async () => {
  await loadData()

  // 同时加载词频相似度数据
  loadWordSimData()

  const queryWord = route.query.word as string
  if (queryWord) {
    searchQuery.value = queryWord
    await performSearch()
  }
})

watch(searchQuery, () => {
  currentPage.value = 1
  performSearch()
})

watch(lengthFilter, () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="wordcount-view">
    <PageHeader title="词频统计" :subtitle="`共收录 ${loadedWords.length.toLocaleString()} 个高频词汇，按使用频率排序`"
      :icon="TextOutline" />

    <NGrid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <NGridItem>
        <StatsCard label="词汇总数" :value="loadedWords.length.toLocaleString()" :prefix-icon="LibraryOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="高频词" :value="loadedWordSimWords.length.toLocaleString()" :prefix-icon="GitNetworkOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="最高频率" :value="topCount.toLocaleString()" suffix="次" :prefix-icon="StarOutline" />
      </NGridItem>
      <NGridItem>
        <StatsCard label="平均长度" :value="avgWordLength" :prefix-icon="ResizeOutline" />
      </NGridItem>
    </NGrid>

    <ChunkLoaderStatus v-if="chunkLoader.isLoading.value || cachedChunksCount > 0"
      :is-loading="chunkLoader.isLoading.value" :is-paused="chunkLoader.isPaused.value"
      :progress="Math.round((loadedChunksCount / (totalChunks || 1)) * 100)" :loaded-count="loadedChunksCount"
      :total-count="totalChunks" title="加载词频数据" :hint="loadingHint" :stats="[
        { label: '已加载词汇', value: loadedWords.length.toLocaleString() + ' 个' },
        { label: '缓存分块', value: cachedChunksCount.toLocaleString() + ' 个' }
      ]" @pause="chunkLoader.pause" @resume="chunkLoader.resume" />

    <ChunkLoaderStatus v-if="wordSimChunkLoader.isLoading.value || wordSimCachedChunksCount > 0"
      :is-loading="wordSimChunkLoader.isLoading.value" :is-paused="wordSimChunkLoader.isPaused.value"
      :progress="Math.round((wordSimLoadedChunksCount / (wordSimTotalChunks || 1)) * 100)"
      :loaded-count="wordSimLoadedChunksCount" :total-count="wordSimTotalChunks" title="加载词频相似度数据"
      :hint="wordSimLoadingHint" :stats="[
        { label: '已加载词汇', value: loadedWordSimWords.length.toLocaleString() + ' 个' },
        { label: '缓存分块', value: wordSimCachedChunksCount.toLocaleString() + ' 个' }
      ]" @pause="wordSimChunkLoader.pause" @resume="wordSimChunkLoader.resume" />

    <WordCloud v-if="isWordCloudReady" :words="wordcloudWords" :max-words="80" :width="700" :height="350" :title="wordCloudTitle"
      :loading="chunkLoader.isLoading.value" @click="handleWordCloudClick" />

    <SearchContainer v-model="searchQuery" placeholder="搜索" :total="displayTotal" :query-time="searchStats.queryTime"
      :source="searchStats.source as any" :loading="isSearching" @search="handleSearch" @clear="clearFilters">
      <template #filters>
        <NSelect v-model:value="lengthFilter" :options="lengthOptions" placeholder="长度" style="width: 130px"
          size="medium" clearable />
      </template>
    </SearchContainer>

    <!-- 加载中状态 -->
    <NEmpty v-if="isInitializing || (loadedWords.length === 0 && hasMoreToLoad && !searchQuery.trim() && !lengthFilter)"
      description="加载中...">
    </NEmpty>

    <!-- 无搜索结果状态 -->
    <NEmpty v-else-if="displayWords.length === 0" :description="hasMoreToLoad ? '加载更多数据可能会有结果' : '没有数据'">
      <template #extra>
        <NButton v-if="hasMoreToLoad" @click="clearFilters">
          清除筛选以查看更多
        </NButton>
        <NButton v-else @click="clearFilters">
          清除筛选
        </NButton>
      </template>
    </NEmpty>

    <div v-else-if="displayWords.length > 0" class="wordcount-container">
      <div class="words-grid">
        <div
          v-for="row in paginatedWordCards"
          :key="`${row.rank}-${row.word}`"
          class="word-card word-card--dense"
          @click="goToKeyword(row.word)"
        >
          <div class="word-card__row word-card__row--main">
            <div
              class="rank-badge"
              :class="{
                'top-ten': row.rank <= 10,
                'rank-1': row.rank === 1,
                'rank-2': row.rank === 2,
                'rank-3': row.rank === 3
              }"
              :title="`排名 ${row.rank}`"
            >
              {{ row.rank }}
            </div>
            <h3 class="word-text">{{ row.word }}</h3>
            <div class="word-card__stats">
              <span class="word-card__freq-num">{{ (row.count ?? 0).toLocaleString() }}</span>
              <span class="word-card__freq-unit">次</span>
              <span class="word-card__sep" aria-hidden="true">·</span>
              <span class="word-card__len">{{ row.word.length }}字</span>
            </div>
          </div>

          <div
            v-if="row.sim.status === 'loading' || row.sim.status === 'has-data'"
            class="word-card__row word-card__row--sim"
          >
            <span class="sim-label">近邻</span>
            <template v-if="row.sim.status === 'loading'">
              <span class="sim-placeholder">解析中…</span>
            </template>
            <div v-else class="sim-chips">
              <NTag
                v-for="sw in row.sim.similarWords.slice(0, 3)"
                :key="sw.word"
                :type="getSimilarityColor(sw.similarity)"
                size="tiny"
                bordered
                class="sim-tag"
              >
                {{ sw.word }}
              </NTag>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-wrapper">
        <NPagination :page="currentPage" :page-count="totalPages" :page-size="pageSize" :page-sizes="[20, 50, 100, 200]"
          show-size-picker show-quick-jumper @update:page="handlePageChange" @update:page-size="handlePageSizeChange" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.wordcount-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.stats-grid {
  margin-bottom: 24px;
}

.search-section {
  margin-bottom: 24px;
}

.wordcount-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(168px, 1fr));
  gap: 8px;
}

.word-card {
  position: relative;
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.word-card--dense {
  padding: 8px 10px;
  min-height: 0;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e8eaed;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
  animation: none;
}

.word-card--dense:hover {
  transform: none;
  background: #fafafa;
  border-color: rgba(139, 38, 53, 0.28);
  box-shadow: 0 0 0 1px rgba(139, 38, 53, 0.08);
}

.word-card--dense::before {
  display: none;
}

.word-card__row--main {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.word-card__row--sim {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 6px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #f1f5f9;
  min-height: 22px;
}

.word-card__stats {
  flex-shrink: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 1px;
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.word-card__sep {
  margin: 0 3px;
  color: #cbd5e1;
  font-weight: 400;
}

.word-card__len {
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
}

.rank-badge {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 5px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #64748b;
  font-weight: 700;
  font-size: 10px;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  transition: background 0.15s ease;
}

.rank-badge.top-ten {
  background: linear-gradient(135deg, #8b2635 0%, #a83246 100%);
  color: #fff;
  box-shadow: none;
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  color: #2c3e50;
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #C0C0C0 0%, #A9A9A9 100%);
  color: #2c3e50;
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%);
  color: #fff;
}

.word-text {
  flex: 1;
  min-width: 0;
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
  font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
  letter-spacing: 0.02em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.word-card__freq-num {
  font-size: 0.8125rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #8b2635;
}

.word-card__freq-unit {
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
}

.sim-label {
  flex-shrink: 0;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #cbd5e1;
}

.sim-placeholder {
  font-size: 10px;
  color: #94a3b8;
}

.sim-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.sim-chips :deep(.n-tag) {
  font-weight: 500;
  line-height: 1.2;
}

.sim-tag {
  padding: 0 5px !important;
  border-radius: 4px !important;
  font-size: 10px !important;
}

.sim-tag:hover {
  transform: none;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
}

@media (max-width: 768px) {
  .wordcount-view {
    padding: 16px;
  }

  .words-grid {
    grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
    gap: 6px;
  }

  .word-card--dense {
    padding: 7px 8px;
  }
}
</style>
