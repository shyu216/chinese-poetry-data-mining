<script setup lang="ts">
/**
 * VirtualPoemList - 虚拟滚动诗词列表
 * 
 * 功能：
 * - 大数据量高性能渲染
 * - 动态高度支持
 * - 平滑滚动体验
 * - 骨架屏loading
 */
import { ref, computed, watch, nextTick } from 'vue'
import { RecycleScroller } from 'vue-virtual-scroller'
import { NCard, NSkeleton } from 'naive-ui'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import PoemCard from '@/components/content/PoemCard.vue'
import type { PoemSummary } from '@/composables/types'

interface Props {
  poems: PoemSummary[]
  loading?: boolean
  loadingMore?: boolean
  hasMore?: boolean
  itemHeight?: number
  buffer?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  loadingMore: false,
  hasMore: false,
  itemHeight: 200,
  buffer: 200
})

const emit = defineEmits<{
  'load-more': []
  'item-click': [poem: PoemSummary]
}>()

const scrollerRef = ref<InstanceType<typeof RecycleScroller> | null>(null)

// 骨架屏数据
const skeletonCount = 6

// 监听滚动到底部
const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  const scrollBottom = target.scrollTop + target.clientHeight
  const threshold = target.scrollHeight - 100
  
  if (scrollBottom >= threshold && props.hasMore && !props.loadingMore) {
    emit('load-more')
  }
}

// 刷新列表
const refresh = () => {
  scrollerRef.value?.updateVisibleItems?.(true)
}

// 滚动到指定位置
const scrollToItem = (index: number) => {
  scrollerRef.value?.scrollToItem?.(index)
}

// 暴露方法
defineExpose({
  refresh,
  scrollToItem
})
</script>

<template>
  <div class="virtual-poem-list">
    <!-- 初始加载骨架屏 -->
    <div v-if="loading && poems.length === 0" class="skeleton-container">
      <NCard
        v-for="i in skeletonCount"
        :key="i"
        class="skeleton-card"
      >
        <div class="skeleton-content">
          <NSkeleton text width="60%" style="margin-bottom: 12px" />
          <NSkeleton text width="40%" style="margin-bottom: 8px" />
          <NSkeleton text :repeat="2" />
        </div>
      </NCard>
    </div>

    <!-- 虚拟滚动列表 -->
    <RecycleScroller
      v-else
      ref="scrollerRef"
      class="scroller"
      :items="poems"
      :item-size="itemHeight"
      :buffer="buffer"
      key-field="id"
      @scroll="handleScroll"
    >
      <template #default="{ item, index, active }">
        <div
          class="poem-item"
          :class="{ 'is-active': active }"
          :style="{ height: `${itemHeight}px` }"
        >
          <PoemCard
            :id="item.id"
            :title="item.title"
            :author="item.author"
            :dynasty="item.dynasty"
            :content="item.content"
            :tags="item.tags"
          />
        </div>
      </template>

      <!-- 底部加载更多 -->
      <template #after>
        <div v-if="loadingMore" class="loading-more">
          <NSkeleton text :repeat="2" />
          <NSkeleton text width="60%" />
        </div>
        <div v-else-if="!hasMore && poems.length > 0" class="no-more">
          <span>—— 已览尽所有诗词 ——</span>
        </div>
      </template>
    </RecycleScroller>

    <!-- 空状态 -->
    <div v-if="!loading && poems.length === 0" class="empty-state">
      <div class="empty-icon">📜</div>
      <p class="empty-text">此处尚无诗词，且去别处寻寻</p>
    </div>
  </div>
</template>

<style scoped>
.virtual-poem-list {
  width: 100%;
  height: 100%;
}

/* 骨架屏 */
.skeleton-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding: 16px;
}

.skeleton-card {
  height: 200px;
}

.skeleton-content {
  padding: 8px 0;
}

/* 虚拟滚动容器 */
.scroller {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.scroller :deep(.vue-recycle-scroller__item-wrapper) {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding: 16px;
}

/* 诗词项 */
.poem-item {
  padding: 0;
  transition: transform 0.2s ease;
}

.poem-item.is-active {
  z-index: 1;
}

/* 加载更多 */
.loading-more {
  grid-column: 1 / -1;
  padding: 24px;
  text-align: center;
}

.no-more {
  grid-column: 1 / -1;
  padding: 32px;
  text-align: center;
  color: var(--color-ink-light, #999);
  font-size: 14px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  color: var(--color-ink-light, #666);
  font-family: "Noto Serif SC", serif;
}

/* 滚动条美化 */
.scroller::-webkit-scrollbar {
  width: 6px;
}

.scroller::-webkit-scrollbar-track {
  background: transparent;
}

.scroller::-webkit-scrollbar-thumb {
  background: rgba(139, 38, 53, 0.2);
  border-radius: 3px;
}

.scroller::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 38, 53, 0.4);
}

/* 响应式 */
@media (max-width: 768px) {
  .skeleton-container,
  .scroller :deep(.vue-recycle-scroller__item-wrapper) {
    grid-template-columns: 1fr;
    padding: 12px;
    gap: 12px;
  }

  .scroller {
    height: calc(100vh - 160px);
  }
}

@media (max-width: 480px) {
  .skeleton-container,
  .scroller :deep(.vue-recycle-scroller__item-wrapper) {
    padding: 8px;
    gap: 8px;
  }
}
</style>
