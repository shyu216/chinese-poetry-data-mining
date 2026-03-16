<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NButton, NIcon } from 'naive-ui'
import { BookmarkOutline, ShareSocialOutline, HeartOutline, HeartSharp } from '@vicons/ionicons5'

interface Props {
  title: string
  author: string
  dynasty: string
  content: string[]
  favorite?: boolean
  bookmarked?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  favorite: false,
  bookmarked: false
})

const emit = defineEmits<{
  favorite: []
  bookmark: []
  share: []
}>()

const formattedContent = computed(() => {
  return props.content.join('\n')
})
</script>

<template>
  <NCard class="poem-display-card" :bordered="false">
    <template #header>
      <div class="poem-header">
        <div class="poem-title-section">
          <h2 class="poem-title">{{ title }}</h2>
          <span class="poem-author">{{ author }} · {{ dynasty }}</span>
        </div>
        <div class="poem-actions">
          <NButton
            quaternary
            circle
            :type="favorite ? 'error' : 'default'"
            @click="emit('favorite')"
          >
            <template #icon>
              <NIcon :component="favorite ? HeartSharp : HeartOutline" />
            </template>
          </NButton>
          <NButton
            quaternary
            circle
            :type="bookmarked ? 'warning' : 'default'"
            @click="emit('bookmark')"
          >
            <template #icon>
              <NIcon :component="BookmarkOutline" />
            </template>
          </NButton>
          <NButton quaternary circle @click="emit('share')">
            <template #icon>
              <NIcon :component="ShareSocialOutline" />
            </template>
          </NButton>
        </div>
      </div>
    </template>
    <div class="poem-content">
      <p v-for="(line, index) in content" :key="index" class="poem-line">
        {{ line }}
      </p>
    </div>
  </NCard>
</template>

<style scoped>
.poem-display-card {
  background: var(--color-bg-paper, #fff);
}

.poem-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.poem-title-section {
  flex: 1;
}

.poem-title {
  font-family: "Noto Serif SC", serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink, #2c3e50);
  margin: 0 0 8px 0;
  text-align: center;
}

.poem-author {
  display: block;
  text-align: center;
  font-size: 14px;
  color: var(--color-ink-light, #666);
}

.poem-actions {
  display: flex;
  gap: 4px;
}

.poem-content {
  padding: 24px 0;
}

.poem-line {
  font-family: "Noto Serif SC", serif;
  font-size: 18px;
  line-height: 2;
  color: var(--color-ink, #2c3e50);
  text-align: center;
  margin: 0;
  letter-spacing: 2px;
}
</style>
