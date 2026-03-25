<!--
  @overview
  file: web/src/views/ClusterDetailView.vue
  category: frontend-page
  tech: Vue 3 + TypeScript + Vue Router + Naive UI
  solved: 承载页面级交互、筛选、展示与路由联动
  data_source: 组合式状态与组件内部状态
  data_flow: 状态输入 -> 组件渲染(NButton, NIcon, ArrowBackOutline) -> 路由联动
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: goBack, goToAuthor；主渲染组件: NButton, NIcon, ArrowBackOutline
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NCard, NTag, NIcon, NButton, NSpin, NEmpty, NGrid, NGi, NStatistic, NAlert } from 'naive-ui'
import { PeopleOutline, BookOutline, RibbonOutline, ArrowBackOutline } from '@vicons/ionicons5'

import { useAuthorClusters } from '@/composables/useAuthorClusters'

const route = useRoute()
const router = useRouter()
const { sortedClusters, loading, error, loadClusters } = useAuthorClusters()

const clusterId = computed(() => parseInt(route.params.id as string))

// 从 sortedClusters 中找到当前聚类
const cluster = computed(() => {
  if (!sortedClusters.value.length) return null
  return sortedClusters.value.find(c => c.id === clusterId.value) || null
})

const clusterName = computed(() => {
  return cluster.value?.name || `流派 ${clusterId.value}`
})

const clusterColor = computed(() => {
  return cluster.value?.color || '#8B2635'
})

const formatNumber = (num: number): string => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

const goBack = () => {
  router.push('/authors/clusters')
}

const goToAuthor = (authorName: string) => {
  router.push(`/authors/${encodeURIComponent(authorName)}`)
}

onMounted(() => {
  if (!sortedClusters.value.length) {
    loadClusters()
  }
})
</script>

<template>
  <div class="cluster-detail-view">
    <!-- 返回按钮 -->
    <div class="back-section">
      <NButton text @click="goBack">
        <template #icon>
          <NIcon :size="20">
            <ArrowBackOutline />
          </NIcon>
        </template>
        返回流派列表
      </NButton>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <NSpin size="large" />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <NAlert type="error" :title="error || ''" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="!cluster" class="empty-container">
      <NEmpty description="流派不存在" />
    </div>

    <!-- 流派详情 -->
    <div v-else class="cluster-content">
      <!-- 流派头部 -->
      <NCard class="header-card" :bordered="false">
        <div class="cluster-header">
          <div class="header-badge" :style="{ background: clusterColor }">
            <NIcon :size="24" color="#fff">
              <RibbonOutline />
            </NIcon>
          </div>
          <div class="header-info">
            <h1 class="cluster-title">{{ clusterName }}</h1>
            <p class="cluster-subtitle">诗人流派分析</p>
          </div>
        </div>

        <!-- 统计信息 -->
        <NGrid :cols="3" :x-gap="16" responsive="screen" class="stats-grid">
          <NGi>
            <NStatistic label="诗人数量" :value="cluster.size">
              <template #prefix>
                <NIcon :size="18" color="var(--color-seal)">
                  <PeopleOutline />
                </NIcon>
              </template>
            </NStatistic>
          </NGi>
          <NGi>
            <NStatistic label="平均诗数" :value="cluster.avg_poems">
              <template #prefix>
                <NIcon :size="18" color="var(--color-seal)">
                  <BookOutline />
                </NIcon>
              </template>
            </NStatistic>
          </NGi>
          <NGi>
            <NStatistic label="特色词汇" :value="cluster.top_words.length">
              <template #prefix>
                <NIcon :size="18" color="var(--color-seal)">
                  <RibbonOutline />
                </NIcon>
              </template>
            </NStatistic>
          </NGi>
        </NGrid>
      </NCard>

      <!-- 代表诗人 -->
      <NCard class="authors-card" :bordered="false" title="代表诗人">
        <div class="authors-list">
          <NTag
            v-for="(author, i) in cluster.representatives"
            :key="i"
            size="large"
            :bordered="false"
            :color="{ color: clusterColor, textColor: '#fff' }"
            class="author-tag"
            @click="goToAuthor(author)"
          >
            {{ author }}
          </NTag>
        </div>
      </NCard>

      <!-- 特色词汇 -->
      <NCard class="words-card" :bordered="false" title="特色词汇">
        <div class="words-grid">
          <div
            v-for="(word, i) in cluster.top_words"
            :key="i"
            class="word-item"
          >
            <span class="word-text">{{ word.word }}</span>
            <span class="word-ratio">{{ word.ratio.toFixed(1) }}x</span>
          </div>
        </div>
      </NCard>

      <!-- 主要诗体 -->
      <NCard class="types-card" :bordered="false" title="主要诗体">
        <div class="types-list">
          <div
            v-for="(item, i) in cluster.poem_types"
            :key="i"
            class="type-item"
          >
            <span class="type-name">{{ item.type }}</span>
            <span class="type-count">{{ formatNumber(item.count) }}</span>
          </div>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.cluster-detail-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.back-section {
  margin-bottom: 24px;
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.cluster-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-card {
  margin-bottom: 8px;
}

.cluster-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.header-badge {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.header-info {
  flex: 1;
}

.cluster-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--color-ink);
}

.cluster-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink-light);
}

.stats-grid {
  margin-top: 20px;
}

.authors-card,
.words-card,
.types-card {
  margin-bottom: 8px;
}

.authors-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.author-tag {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.author-tag:hover {
  transform: translateY(-2px);
}

.words-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.word-item {
  background: var(--color-bg-paper);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.word-item:hover {
  border-color: var(--color-accent);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.word-text {
  display: block;
  font-size: 16px;
  font-weight: 500;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.word-ratio {
  font-size: 12px;
  color: var(--color-accent);
}

.types-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.type-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-bg-paper);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.type-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-ink);
}

.type-count {
  font-size: 14px;
  color: var(--color-ink-light);
}

/* 响应式 */
@media (max-width: 768px) {
  .cluster-detail-view {
    padding: 16px;
  }

  .back-section {
    margin-bottom: 16px;
  }

  .cluster-header {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .header-badge {
    width: 64px;
    height: 64px;
  }

  .cluster-title {
    font-size: 22px;
  }

  .cluster-subtitle {
    font-size: 13px;
  }

  .words-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .word-item {
    padding: 12px;
  }

  .word-text {
    font-size: 14px;
  }
}
</style>
