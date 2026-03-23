<script setup lang="ts">
interface Props {
  topOffset?: number
  bottomOffset?: number
  leftOffset?: number
  rightOffset?: number
  animationDuration?: number
  animationDelay?: number
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  topOffset: 28,
  bottomOffset: 28,
  leftOffset: 28,
  rightOffset: 28,
  animationDuration: 5,
  animationDelay: 0,
  color: 'var(--color-border, #e8e8e8)'
})
</script>

<template>
  <div class="breathing-frame">
    <div
      class="frame-line frame-top"
      :style="{
        top: `${topOffset}px`,
        left: `${leftOffset + 52}px`,
        right: `${rightOffset + 52}px`,
        background: color,
        animationDuration: `${animationDuration}s`,
        animationDelay: `${animationDelay}s`
      }"
    />
    <div
      class="frame-line frame-bottom"
      :style="{
        bottom: `${bottomOffset}px`,
        left: `${leftOffset + 52}px`,
        right: `${rightOffset + 52}px`,
        background: color,
        animationDuration: `${animationDuration}s`,
        animationDelay: `${animationDelay + 0.2}s`
      }"
    />
    <div
      class="frame-line frame-left"
      :style="{
        left: `${leftOffset}px`,
        top: `${topOffset + 52}px`,
        bottom: `${bottomOffset + 52}px`,
        background: color,
        animationDuration: `${animationDuration}s`,
        animationDelay: `${animationDelay + 0.1}s`
      }"
    />
    <div
      class="frame-line frame-right"
      :style="{
        right: `${rightOffset}px`,
        top: `${topOffset + 52}px`,
        bottom: `${bottomOffset + 52}px`,
        background: color,
        animationDuration: `${animationDuration}s`,
        animationDelay: `${animationDelay + 0.3}s`
      }"
    />
  </div>
</template>

<style scoped>
.breathing-frame {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}

.frame-line {
  position: absolute;
  opacity: 0.5;
  animation: frameBreathe ease-in-out infinite;
}

.frame-top,
.frame-bottom {
  height: 1px;
}

.frame-left,
.frame-right {
  width: 1px;
}

@keyframes frameBreathe {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
