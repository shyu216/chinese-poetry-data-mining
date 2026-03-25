<!--
  @overview
  file: web/src/components/author/AuthorCard.vue
  category: frontend-component
  tech: Vue 3 + TypeScript + Vue Router + Naive UI
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(NCard, NAvatar, NEllipsis) -> 路由联动
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: goToDetail, goToAuthors；主渲染组件: NCard, NAvatar, NEllipsis, DynastyBadge
<!--
  文件: web/src/components/author/AuthorCard.vue
  说明: 作者展示卡片组件，接受父组件传入的作者信息（props），负责展示头像、朝代、作品数与标签，并提供跳转到作者详情或按朝代筛选的交互。

  数据管线:
    - 输入: 通过 `props` 接收 `author`, `dynasty`, `poemCount`, `avatar`, `rank`, `tags`。
    - 处理: 局部计算（如 `initials`）与路由跳转逻辑；不在组件内发起网络请求。
    - 输出: 通过路由跳转将用户引导到详情页或列表页。

  复杂度:
    - 渲染成本为 O(1)（单个卡片），当父组件通过 `v-for` 渲染 n 个卡片时为 O(n)。
    - 空间: 按卡片常数占用，若包含图片资源则依赖浏览器缓存与图片体积。

  使用技术/要点:
    - Vue 3 组合式语法 + TypeScript，Naive UI 组件（NCard, NAvatar, NTag 等）。
    - 使用 `NEllipsis` 限制行数，`encodeURIComponent` 安全构造路由参数。
    - `goToAuthors` 中使用 `e.stopPropagation()` 防止 click 事件冒泡到父容器。

  潜在问题:
    - 若父组件渲染大量卡片（数千级别），需配合虚拟列表避免 DOM 过多导致卡顿。
    - 头像图片未做懒加载或占位策略，可能导致首屏加载压力。
    - props 未做复杂校验（仅 TS 类型），运行时仍需确保数据完整性。
    - 可访问性(ARIA)与键盘交互未明确处理，需补充以提升无障碍支持。
-->
  poemCount: number
  avatar?: string
  rank?: number
  tags?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  poemCount: 0
})

const router = useRouter()

const initials = computed(() => {
  return props.author.slice(0, 2)
})

const goToDetail = () => {
  router.push(`/author/${encodeURIComponent(props.author)}`)
}

const goToAuthors = (e: Event) => {
  e.stopPropagation()
  router.push(`/authors?dynasty=${encodeURIComponent(props.dynasty)}`)
}
</script>

<template>
  <NCard 
    class="author-card" 
    hoverable 
    @click="goToDetail"
  >
    <div class="author-card-content">
      <div class="author-avatar">
        <NAvatar 
          v-if="avatar" 
          :src="avatar" 
          :size="64" 
          round
        />
        <NAvatar v-else :size="64" round>
          {{ initials }}
        </NAvatar>
        <span v-if="rank" class="rank-badge">{{ rank }}</span>
      </div>

      <div class="author-info">
        <div class="author-header">
          <h3 class="author-name">
            <NEllipsis :line-clamp="1">{{ author }}</NEllipsis>
          </h3>
          <DynastyBadge :dynasty="dynasty" size="small" />
        </div>

        <div class="author-stats">
          <div class="stat-item">
            <BookOutline class="stat-icon" />
            <span class="stat-value">{{ poemCount }}</span>
            <span class="stat-label">首</span>
          </div>
        </div>

        <div v-if="tags?.length" class="author-tags">
          <NTag 
            v-for="tag in tags.slice(0, 2)" 
            :key="tag" 
            size="small" 
            :bordered="false"
            type="warning"
          >
            {{ tag }}
          </NTag>
        </div>
      </div>
    </div>

    <template #action>
      <div class="card-action" @click="goToAuthors">
        <PersonOutline />
        <span>同诗人</span>
      </div>
    </template>
  </NCard>
</template>

<style scoped>
.author-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.author-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-seal, #8b2635);
}

.author-card-content {
  display: flex;
  gap: 16px;
}

.author-avatar {
  position: relative;
  flex-shrink: 0;
}

.author-avatar :deep(.n-avatar) {
  background: linear-gradient(135deg, var(--color-seal, #8b2635), #a63d4d);
  color: #fff;
  font-family: "Noto Serif SC", serif;
  font-size: 20px;
  font-weight: 600;
}

.rank-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: var(--color-seal, #8b2635);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.author-info {
  flex: 1;
  min-width: 0;
}

.author-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.author-name {
  margin: 0;
  font-family: "Noto Serif SC", "Source Han Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
  flex: 1;
  min-width: 0;
}

.author-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-ink-light, #666);
}

.stat-icon {
  font-size: 14px;
  color: var(--color-seal, #8b2635);
}

.stat-value {
  font-weight: 600;
  color: var(--color-ink, #2c3e50);
}

.author-tags {
  display: flex;
  gap: 6px;
}

.card-action {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-ink-light, #666);
  cursor: pointer;
}

.card-action:hover {
  color: var(--color-seal, #8b2635);
}

:deep(.n-card__action) {
  padding: 8px 12px;
}
</style>
