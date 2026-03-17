<script setup lang="ts">
import { computed } from 'vue'
import { NAvatar, NTag, NProgress } from 'naive-ui'

interface Props {
  name: string
  dynasty: string
  avatar?: string
  poemCount: number
  maxCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxCount: 500
})

const initials = computed(() => props.name.slice(0, 2))

const progressPercent = computed(() => {
  return Math.min(100, (props.poemCount / props.maxCount) * 100)
})
</script>

<template>
  <div class="author-mini-card">
    <NAvatar
      v-if="avatar"
      :src="avatar"
      :size="40"
      round
    />
    <NAvatar v-else :size="40" round>
      {{ initials }}
    </NAvatar>
    <div class="author-info">
      <span class="author-name">{{ name }}</span>
      <span class="author-dynasty">{{ dynasty }}</span>
    </div>
    <div class="author-progress">
      <span class="poem-count">{{ poemCount }}首</span>
      <NProgress
        type="line"
        :percentage="progressPercent"
        :show-indicator="false"
        :height="4"
      />
    </div>
  </div>
</template>

<style scoped>
.author-mini-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--color-bg-paper, #fff);
  border: 1px solid var(--color-border, #e8e8e8);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.author-mini-card:hover {
  border-color: var(--color-seal, #8b2635);
  box-shadow: 0 2px 8px rgba(139, 38, 53, 0.1);
}

.author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-ink, #2c3e50);
}

.author-dynasty {
  font-size: 12px;
  color: var(--color-ink-light, #999);
}

.author-progress {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 60px;
}

.poem-count {
  font-size: 12px;
  color: var(--color-ink-light, #666);
}
</style>
