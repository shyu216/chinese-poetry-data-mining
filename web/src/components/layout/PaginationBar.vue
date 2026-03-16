<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NButton, NIcon, NBadge } from 'naive-ui'
import { ChevronBackOutline, ChevronForwardOutline, LayersOutline } from '@vicons/ionicons5'

interface Props {
  currentPage: number
  totalPages: number
  pageSize?: number
  total?: number
  showPageSize?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  pageSize: 20,
  showPageSize: false
})

const emit = defineEmits<{
  'update:currentPage': [page: number]
}>()

const pageNumbers = computed(() => {
  const pages: (number | string)[] = []
  const total = props.totalPages
  const current = props.currentPage
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    
    for (let i = start; i <= end; i++) pages.push(i)
    
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }
  
  return pages
})

const goToPage = (page: number | string) => {
  if (typeof page === 'number' && page !== props.currentPage) {
    emit('update:currentPage', page)
  }
}
</script>

<template>
  <div class="pagination-bar">
    <NButton
      :disabled="currentPage <= 1"
      @click="goToPage(currentPage - 1)"
    >
      <template #icon>
        <NIcon :component="ChevronBackOutline" />
      </template>
    </NButton>
    
    <div class="page-numbers">
      <NButton
        v-for="page in pageNumbers"
        :key="page"
        :type="page === currentPage ? 'primary' : 'default'"
        :quaternary="page !== currentPage"
        size="small"
        :disabled="page === '...'"
        @click="goToPage(page)"
      >
        {{ page }}
      </NButton>
    </div>
    
    <NButton
      :disabled="currentPage >= totalPages"
      @click="goToPage(currentPage + 1)"
    >
      <template #icon>
        <NIcon :component="ChevronForwardOutline" />
      </template>
    </NButton>
    
    <span v-if="total" class="page-info">
      共 {{ total }} 条
    </span>
  </div>
</template>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-info {
  margin-left: 16px;
  font-size: 13px;
  color: var(--color-ink-light, #666);
}
</style>
