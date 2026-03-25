<!--
  @overview
  file: web/src/components/ui/decorative/BreathingFrame.vue
  category: frontend-component / decorative
  tech: Vue 3 + TypeScript + CSS
  summary: 页面边框呼吸动画组件，提供简单的边框线条动画以增强视觉层次。

  Data pipeline (conceptual):
  - 输入: 通过 props 提供边距、动画时长与颜色等配置
  - 处理: 计算样式并渲染四条边框线，使用 CSS 动画控制透明度/节奏
  - 输出: 纯表现组件，不参与数据加载

  Complexity & notes:
  - 渲染与计算成本为 O(1)。若在同一页面大量使用，请审视动画数量对渲染性能的影响

  Recommendations:
  - 在低性能设备上可禁用动画或降低帧率/样式复杂度
 -->
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
