<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NTabs, NTabPane, NButton, NSpace, NGrid, NGi } from 'naive-ui'

import SearchBar from '@/components/common/SearchBar.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

import PoemTypeBadge from '@/components/poem/PoemTypeBadge.vue'
import PoemDisplayCard from '@/components/poem/PoemDisplayCard.vue'
import MeterPatternCard from '@/components/poem/MeterPatternCard.vue'

import AuthorMiniCard from '@/components/author/AuthorMiniCard.vue'

import StatsOverview from '@/components/data/StatsOverview.vue'

import PaginationBar from '@/components/layout/PaginationBar.vue'
import TabNavigation from '@/components/layout/TabNavigation.vue'

import DynastyBadge from '@/components/DynastyBadge.vue'
import KeywordTag from '@/components/KeywordTag.vue'
import StatsCard from '@/components/StatsCard.vue'

const currentPage = ref(1)
const totalPages = ref(10)

const activeTab = ref('common')

const tabs = [
  { name: 'common', label: '通用组件' },
  { name: 'poem', label: '诗词组件' },
  { name: 'author', label: '作者组件' },
  { name: 'data', label: '数据组件' },
  { name: 'layout', label: '布局组件' },
  { name: 'original', label: '原有组件' }
]

const handleSearch = (value: string) => {
  console.log('搜索:', value)
}

const handleFilter = (dynasty: string) => {
  console.log('筛选:', dynasty)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const poemContent = [
  '床前明月光，',
  '疑是地上霜。',
  '举头望明月，',
  '低头思故乡。'
]

const favorite = ref(false)
const bookmarked = ref(false)

const toggleFavorite = () => {
  favorite.value = !favorite.value
}

const toggleBookmark = () => {
  bookmarked.value = !bookmarked.value
}
</script>

<template>
  <div class="component-demo">
    <div class="demo-header">
      <h1>组件演示中心</h1>
      <p>展示系统中各类可复用的 Vue 组件</p>
    </div>

    <NTabs v-model:value="activeTab" type="line" animated>
      <NTabPane name="common" tab="通用组件">
        <div class="demo-section">
          <NCard title="SearchBar 搜索栏" class="demo-card">
            <SearchBar
              placeholder="搜索诗词、作者..."
              :show-dynasty-filter="true"
              @search="handleSearch"
              @filter="handleFilter"
            />
          </NCard>

          <NCard title="LoadingSpinner 加载动画" class="demo-card">
            <NSpace>
              <LoadingSpinner size="small" tip="加载中..." />
              <LoadingSpinner size="medium" />
              <LoadingSpinner size="large" tip="正在获取数据..." />
            </NSpace>
          </NCard>

          <NCard title="EmptyState 空状态" class="demo-card">
            <NSpace vertical>
              <EmptyState type="no-data" />
              <EmptyState type="not-found" />
              <EmptyState type="error" />
            </NSpace>
          </NCard>
        </div>
      </NTabPane>

      <NTabPane name="poem" tab="诗词组件">
        <div class="demo-section">
          <NCard title="PoemTypeBadge 诗词类型标签" class="demo-card">
            <NSpace>
              <PoemTypeBadge type="shi" />
              <PoemTypeBadge type="ci" label="词" />
              <PoemTypeBadge type="lv" label="律诗" />
            </NSpace>
          </NCard>

          <NCard title="PoemDisplayCard 诗词展示卡片" class="demo-card">
            <PoemDisplayCard
              title="静夜思"
              author="李白"
              dynasty="唐"
              :content="poemContent"
              :favorite="favorite"
              :bookmarked="bookmarked"
              @favorite="toggleFavorite"
              @bookmark="toggleBookmark"
            />
          </NCard>

          <NCard title="MeterPatternCard 格律卡片" class="demo-card">
            <MeterPatternCard
              meter="五言绝句"
              pattern="仄仄平平仄，平平仄仄平"
              tone-pattern="仄仄平平仄平平仄仄平"
            />
          </NCard>
        </div>
      </NTabPane>

      <NTabPane name="author" tab="作者组件">
        <div class="demo-section">
          <NCard title="AuthorMiniCard 作者迷你卡片" class="demo-card">
            <NSpace vertical>
              <AuthorMiniCard
                name="李白"
                dynasty="唐"
                :poem-count="320"
                :max-count="500"
              />
              <AuthorMiniCard
                name="杜甫"
                dynasty="唐"
                :poem-count="280"
                :max-count="500"
              />
              <AuthorMiniCard
                name="苏轼"
                dynasty="宋"
                :poem-count="450"
                :max-count="500"
              />
            </NSpace>
          </NCard>
        </div>
      </NTabPane>

      <NTabPane name="data" tab="数据组件">
        <div class="demo-section">
          <NCard title="StatsOverview 数据概览" class="demo-card">
            <StatsOverview
              :total-poems="52000"
              :total-authors="6800"
              :total-dynasties="12"
            />
          </NCard>
        </div>
      </NTabPane>

      <NTabPane name="layout" tab="布局组件">
        <div class="demo-section">
          <NCard title="PaginationBar 分页组件" class="demo-card">
            <PaginationBar
              v-model:current-page="currentPage"
              :total-pages="totalPages"
              :total="200"
            />
          </NCard>

          <NCard title="TabNavigation 标签导航" class="demo-card">
            <TabNavigation
              :tabs="tabs"
              :active-name="activeTab"
            />
          </NCard>
        </div>
      </NTabPane>

      <NTabPane name="original" tab="原有组件">
        <div class="demo-section">
          <NCard title="DynastyBadge 朝代标签" class="demo-card">
            <NSpace>
              <DynastyBadge dynasty="唐" />
              <DynastyBadge dynasty="宋" />
              <DynastyBadge dynasty="元" />
              <DynastyBadge dynasty="明" />
              <DynastyBadge dynasty="清" />
            </NSpace>
          </NCard>

          <NCard title="KeywordTag 关键词标签" class="demo-card">
            <NSpace>
              <KeywordTag keyword="山水" :count="1250" />
              <KeywordTag keyword="离别" type="warning" :count="856" />
              <KeywordTag keyword="思乡" type="error" :count="642" />
              <KeywordTag keyword="咏物" type="success" :count="980" />
            </NSpace>
          </NCard>

          <NCard title="StatsCard 统计卡片" class="demo-card">
            <NGrid :cols="3" :x-gap="16" :y-gap="16">
              <NGi>
                <StatsCard
                  label="诗词总数"
                  :value="52000"
                  trend="up"
                />
              </NGi>
              <NGi>
                <StatsCard
                  label="作者人数"
                  :value="6800"
                  trend="neutral"
                />
              </NGi>
              <NGi>
                <StatsCard
                  label="朝代数量"
                  :value="12"
                  trend="up"
                />
              </NGi>
            </NGrid>
          </NCard>
        </div>
      </NTabPane>
    </NTabs>
  </div>
</template>

<style scoped>
.component-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.demo-header {
  margin-bottom: 24px;
}

.demo-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink, #2c3e50);
  margin: 0 0 8px 0;
}

.demo-header p {
  font-size: 14px;
  color: var(--color-ink-light, #666);
  margin: 0;
}

.demo-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.demo-card {
  background: var(--color-bg-paper, #fff);
}

.demo-card :deep(.n-card-header) {
  font-weight: 600;
}
</style>
