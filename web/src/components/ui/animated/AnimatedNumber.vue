<!--
  @overview
  file: web/src/components/ui/animated/AnimatedNumber.vue
  category: frontend-component
  tech: Vue 3 + TypeScript
  solved: 提供可复用展示组件与局部交互单元
  data_source: 父组件 props
  data_flow: 状态输入 -> 组件渲染(UI 组件)
  complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
  unique: 关键函数: animate, updateNumber
-->
<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

interface Props {
  value: number
  duration?: number
  delay?: number
  startOnMount?: boolean
  formatter?: (value: number) => string
}

const props = withDefaults(defineProps<Props>(), {
  duration: 1500,
  delay: 0,
  startOnMount: false,
  formatter: (value: number) => value.toLocaleString()
})

const displayValue = ref(0)
const isAnimating = ref(false)

const easeOutQuart = (t: number): number => {
  return 1 - Math.pow(1 - t, 4)
}

const animate = (targetValue: number) => {
  if (isAnimating.value) return

  isAnimating.value = true
  const startValue = 0 // 总是从 0 开始动画
  const startTime = performance.now()

  const updateNumber = (currentTime: number) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / props.duration, 1)
    const easedProgress = easeOutQuart(progress)

    displayValue.value = Math.floor(startValue + (targetValue - startValue) * easedProgress)

    if (progress < 1) {
      requestAnimationFrame(updateNumber)
    } else {
      displayValue.value = targetValue
      isAnimating.value = false
    }
  }

  setTimeout(() => {
    requestAnimationFrame(updateNumber)
  }, props.delay)
}

watch(() => props.value, (newValue) => {
  // 只有当 startOnMount 为 true 时，才在 value 变化时触发动画
  if (props.startOnMount) {
    animate(newValue)
  }
}, { immediate: false })

onMounted(() => {
  if (props.startOnMount) {
    animate(props.value)
  } else {
    // 当 startOnMount 为 false 时，保持 displayValue 为 0
    displayValue.value = 0
  }
})

defineExpose({
  animate,
  displayValue
})
</script>

<template>
  <span class="animated-number">{{ formatter(displayValue) }}</span>
</template>

<style scoped>
.animated-number {
  font-variant-numeric: tabular-nums;
}
</style>
