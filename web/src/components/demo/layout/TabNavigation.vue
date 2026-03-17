<script setup lang="ts">
import { computed } from 'vue'
import { NTabs, NTabPane } from 'naive-ui'

interface Props {
  tabs: Array<{ name: string; label: string; disabled?: boolean }>
  activeName?: string
}

const props = withDefaults(defineProps<Props>(), {
  activeName: ''
})

const emit = defineEmits<{
  'update:activeName': [name: string]
}>()

const handleUpdate = (name: string) => {
  emit('update:activeName', name)
}
</script>

<template>
  <NTabs
    :value="activeName"
    type="line"
    animated
    @update:value="handleUpdate"
  >
    <NTabPane
      v-for="tab in tabs"
      :key="tab.name"
      :name="tab.name"
      :label="tab.label"
      :disabled="tab.disabled"
    />
  </NTabs>
</template>
