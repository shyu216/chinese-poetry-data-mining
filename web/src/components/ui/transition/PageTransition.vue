<script setup lang="ts">
/**
 * PageTransition - 页面过渡动画组件
 * 
 * 提供优雅的页面切换动画效果
 */
import { computed } from 'vue'

interface Props {
  name?: 'fade' | 'slide-left' | 'slide-right' | 'slide-up' | 'ink-spread'
  mode?: 'default' | 'out-in' | 'in-out'
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  name: 'fade',
  mode: 'out-in',
  duration: 400
})

const transitionName = computed(() => `page-${props.name}`)
const transitionDuration = computed(() => `${props.duration}ms`)
</script>

<template>
  <Transition
    :name="transitionName"
    :mode="mode"
    appear
  >
    <slot />
  </Transition>
</template>

<style scoped>
/* ========== 淡入淡出 ========== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all v-bind(transitionDuration) cubic-bezier(0.4, 0, 0.2, 1);
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* ========== 左滑入 ========== */
.page-slide-left-enter-active,
.page-slide-left-leave-active {
  transition: all v-bind(transitionDuration) cubic-bezier(0.4, 0, 0.2, 1);
}

.page-slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* ========== 右滑入 ========== */
.page-slide-right-enter-active,
.page-slide-right-leave-active {
  transition: all v-bind(transitionDuration) cubic-bezier(0.4, 0, 0.2, 1);
}

.page-slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.page-slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* ========== 上滑入 ========== */
.page-slide-up-enter-active,
.page-slide-up-leave-active {
  transition: all v-bind(transitionDuration) cubic-bezier(0.4, 0, 0.2, 1);
}

.page-slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* ========== 水墨扩散 ========== */
.page-ink-spread-enter-active {
  transition: all v-bind(transitionDuration) cubic-bezier(0.4, 0, 0.2, 1);
}

.page-ink-spread-leave-active {
  transition: all calc(v-bind(transitionDuration) * 0.5) ease;
}

.page-ink-spread-enter-from {
  opacity: 0;
  filter: blur(10px);
  transform: scale(0.98);
}

.page-ink-spread-leave-to {
  opacity: 0;
  filter: blur(5px);
}
</style>
