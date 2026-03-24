<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NAvatar, NStatistic, NProgress, NTag, NEllipsis } from 'naive-ui'
import { BookOutline, PersonOutline, FlameOutline } from '@vicons/ionicons5'
import { DynastyBadge } from '@/components/ui/badge'

interface Props {
  author: string
  dynasty: string
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
