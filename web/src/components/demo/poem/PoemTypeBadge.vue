<script setup lang="ts">
import { computed } from 'vue'
import { NTag } from 'naive-ui'

interface Props {
  type?: 'ci' | 'lv' | 'shi'
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'shi'
})

const typeConfig = computed(() => {
  const configs = {
    'ci': { text: '词', color: '#1E40AF', bg: 'rgba(30, 64, 175, 0.08)' },
    'lv': { text: '律诗', color: '#047857', bg: 'rgba(4, 120, 87, 0.08)' },
    'shi': { text: '古体诗', color: '#B45309', bg: 'rgba(180, 83, 9, 0.08)' }
  }
  return configs[props.type]
})
</script>

<template>
  <NTag
    :bordered="false"
    :style="{
      background: typeConfig.bg,
      color: typeConfig.color
    }"
    size="small"
  >
    {{ label || typeConfig.text }}
  </NTag>
</template>
