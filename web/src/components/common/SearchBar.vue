<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NInput, NButton, NSelect, NIcon } from 'naive-ui'
import { SearchOutline, FilterOutline } from '@vicons/ionicons5'

interface Props {
  placeholder?: string
  showDynastyFilter?: boolean
  dynastyOptions?: Array<{ label: string; value: string }>
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索诗词、作者...',
  showDynastyFilter: false,
  dynastyOptions: () => [
    { label: '全部朝代', value: '' },
    { label: '唐', value: '唐' },
    { label: '宋', value: '宋' },
    { label: '元', value: '元' },
    { label: '明', value: '明' },
    { label: '清', value: '清' }
  ]
})

const emit = defineEmits<{
  search: [value: string]
  filter: [dynasty: string]
}>()

const router = useRouter()
const searchValue = ref('')
const selectedDynasty = ref<string | null>(null)

const handleSearch = () => {
  emit('search', searchValue.value)
}

const handleDynastyChange = (value: string | null) => {
  selectedDynasty.value = value
  emit('filter', value || '')
}

const isSearching = computed(() => searchValue.value.length > 0)
</script>

<template>
  <div class="search-bar">
    <div class="search-input-wrapper">
      <NInput
        v-model:value="searchValue"
        :placeholder="placeholder"
        clearable
        size="large"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <NIcon :component="SearchOutline" />
        </template>
      </NInput>
      <NButton
        type="primary"
        size="large"
        :disabled="!searchValue"
        @click="handleSearch"
      >
        搜索
      </NButton>
    </div>
    <div v-if="showDynastyFilter" class="search-filter">
      <NIcon :component="FilterOutline" class="filter-icon" />
      <NSelect
        v-model:value="selectedDynasty"
        :options="dynastyOptions"
        placeholder="筛选朝代"
        clearable
        style="width: 140px"
        @update:value="handleDynastyChange"
      />
    </div>
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
}

.search-input-wrapper :deep(.n-input) {
  flex: 1;
}

.search-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-icon {
  color: var(--color-ink-light, #999);
}
</style>
