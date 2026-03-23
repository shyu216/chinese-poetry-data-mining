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
  startOnMount: true,
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
  const startValue = displayValue.value
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
  animate(newValue)
}, { immediate: false })

onMounted(() => {
  if (props.startOnMount) {
    animate(props.value)
  } else {
    displayValue.value = props.value
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
