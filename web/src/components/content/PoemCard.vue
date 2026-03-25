<!--
  @overview
  file: web/src/components/content/PoemCard.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Vue Router + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(NCard, NIcon, Heart) -> 路由联动
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: goToDetail, goToAuthor, copyPoem, toggleFavorite；主渲染组件: NCard, NIcon, Heart, HeartOutline
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NTag, NButton, NEllipsis, NIcon, useMessage } from 'naive-ui'
import { BookmarkOutline, CopyOutline, HeartOutline, Heart } from '@vicons/ionicons5'
import { DynastyBadge } from '@/components/ui/badge'

interface Props {
  id: string
  title: string
  author: string
  dynasty: string
  content?: string
  tags?: string[]
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true
})

const router = useRouter()
const message = useMessage()

// 收藏状态（本地存储）
const isFavorited = ref(false)

const excerpt = computed(() => {
  if (props.content) {
    return props.content.split('\n').slice(0, 2).join(' / ')
  }
  return ''
})

const goToDetail = () => {
  router.push(`/poem/${props.id}`)
}

const goToAuthor = (e: Event) => {
  e.stopPropagation()
  router.push(`/authors/${encodeURIComponent(props.author)}`)
}

const copyPoem = (e: Event) => {
  e.stopPropagation()
  const text = `${props.title}\n${props.author}〔${props.dynasty}〕\n\n${props.content || ''}`
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制')
  })
}

const toggleFavorite = (e: Event) => {
  e.stopPropagation()
  isFavorited.value = !isFavorited.value
  message.success(isFavorited.value ? '收藏' : '已收藏')
  // TODO: 持久化到本地存储
}
</script>

<template>
  <div class="poem-card-wrapper">
    <NCard 
      class="poem-card" 
      hoverable 
      @click="goToDetail"
    >
      <!-- 水墨纹理背景 -->
      <div class="ink-texture"></div>
      
      <!-- 收藏按钮 -->
      <div class="favorite-btn" @click="toggleFavorite">
        <NIcon :size="20" :class="{ 'is-favorited': isFavorited }">
          <Heart v-if="isFavorited" />
          <HeartOutline v-else />
        </NIcon>
      </div>

      <template #header>
        <div class="poem-card-header">
          <h3 class="poem-title">
            <NEllipsis :line-clamp="1">{{ title || '无题' }}</NEllipsis>
          </h3>
          <DynastyBadge :dynasty="dynasty" size="small" />
        </div>
      </template>

      <div class="poem-body">
        <p v-if="excerpt" class="poem-excerpt">
          <NEllipsis :line-clamp="2" :line-height="22">{{ excerpt }}</NEllipsis>
        </p>
        
        <div class="poem-meta">
          <span class="author-name" @click="goToAuthor">{{ author }}</span>
        </div>

        <div v-if="tags?.length" class="poem-tags">
          <NTag 
            v-for="tag in tags.slice(0, 3)" 
            :key="tag" 
            size="small" 
            :bordered="false"
            type="info"
          >
            {{ tag }}
          </NTag>
          <NTag v-if="tags.length > 3" size="small" :bordered="false" type="default">
            +{{ tags.length - 3 }}
          </NTag>
        </div>
      </div>

      <template v-if="showActions" #action>
        <NButton quaternary size="small" @click="goToAuthor">
            <template #icon>
              <BookmarkOutline />
            </template>
            作者详情
          </NButton>
        <NButton quaternary size="small" @click="copyPoem">
          <template #icon>
            <CopyOutline />
          </template>
          复制
        </NButton>
      </template>
    </NCard>
  </div>
</template>

<style scoped>
/* 3D Tilt Hover 容器 */
.poem-card-wrapper {
  perspective: 1000px;
  transform-style: preserve-3d;
}

.poem-card {
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  transform-style: preserve-3d;
}

/* 3D Tilt Hover 效果 */
.poem-card:hover {
  transform: translateY(-4px) rotateX(2deg) rotateY(-2deg);
  box-shadow: 
    0 12px 40px rgba(139, 38, 53, 0.12),
    0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--color-seal, #8b2635);
}

/* 水墨纹理背景 */
.ink-texture {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.4s ease;
  background: 
    radial-gradient(ellipse at 20% 30%, rgba(139, 38, 53, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 70%, rgba(92, 82, 68, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(139, 38, 53, 0.02) 0%, transparent 70%);
}

.poem-card:hover .ink-texture {
  opacity: 1;
}

/* 收藏按钮 */
.favorite-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  cursor: pointer;
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.poem-card:hover .favorite-btn {
  opacity: 1;
  transform: scale(1);
}

.favorite-btn:hover {
  background: rgba(139, 38, 53, 0.1);
  transform: scale(1.1) !important;
}

.favorite-btn .n-icon {
  color: var(--color-ink-light, #999);
  transition: all 0.3s ease;
}

.favorite-btn .n-icon.is-favorited {
  color: var(--color-seal, #8b2635);
  animation: heartBeat 0.6s ease;
}

@keyframes heartBeat {
  0%, 100% { transform: scale(1); }
  25% { transform: scale(1.2); }
  50% { transform: scale(1); }
  75% { transform: scale(1.15); }
}

.poem-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.poem-title {
  margin: 0;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  flex: 1;
  min-width: 0;
  transition: color 0.3s ease;
}

.poem-card:hover .poem-title {
  color: var(--color-seal, #8b2635);
}

.poem-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.poem-excerpt {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink-light, #666);
  line-height: 22px;
  transition: color 0.3s ease;
}

.poem-card:hover .poem-excerpt {
  color: var(--color-ink, #4a4a4a);
}

.poem-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-size: 14px;
  color: var(--color-seal, #8b2635);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.author-name::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--color-seal, #8b2635);
  transition: width 0.3s ease;
}

.author-name:hover {
  opacity: 0.8;
}

.author-name:hover::after {
  width: 100%;
}

.poem-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

:deep(.n-card__action) {
  padding: 8px 12px;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .poem-card:hover {
    transform: translateY(-2px);
  }
  
  .favorite-btn {
    opacity: 1;
    transform: scale(1);
    top: 8px;
    right: 8px;
    width: 32px;
    height: 32px;
  }
}
</style>
