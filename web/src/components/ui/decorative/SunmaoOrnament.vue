<script setup lang="ts">
import { onMounted } from 'vue'

interface Props {
  position: 'tl' | 'tr' | 'bl' | 'br'
  size?: number
  animationDelay?: number
}

onMounted(() => {
  console.log('[SunmaoOrnament] mounted, position:', props.position)
})

const props = withDefaults(defineProps<Props>(), {
  size: 64,
  animationDelay: 0
})

const positionClasses = {
  tl: 'sunmao-tl',
  tr: 'sunmao-tr',
  bl: 'sunmao-bl',
  br: 'sunmao-br'
}

// 获取连接点坐标（所有元素的基准点）
const getJointXY = () => {
  switch (props.position) {
    case 'tl':
      return { x: 36, y: 36 }
    case 'tr':
      return { x: 56, y: 36 }
    case 'bl':
      return { x: 36, y: 56 }
    case 'br':
      return { x: 56, y: 56 }
  }
}

// 水平梁：从连接点向左右延伸，稍微偏移形成交错
const getBeamH = () => {
  const joint = getJointXY()
  // 水平梁稍微向上偏移，形成交错效果
  const offsetY = -2
  switch (props.position) {
    case 'tl':
    case 'bl':
      // 向左延伸：从左边到连接点右侧
      return { x: 0, y: joint.y + offsetY, width: joint.x + 8 }
    case 'tr':
    case 'br':
      // 向右延伸：从连接点左侧到右边
      return { x: joint.x, y: joint.y + offsetY, width: 100 - joint.x }
  }
}

// 垂直梁：从连接点向上下延伸，稍微偏移形成交错
const getBeamV = () => {
  const joint = getJointXY()
  // 垂直梁稍微向右偏移，形成交错效果
  const offsetX = 2
  switch (props.position) {
    case 'tl':
    case 'tr':
      // 向上延伸：从上边到连接点底部
      return { x: joint.x + offsetX, y: 0, width: 8, height: joint.y + 8 }
    case 'bl':
    case 'br':
      // 向下延伸：从连接点顶部到下边
      return { x: joint.x + offsetX, y: joint.y, width: 8, height: 100 - joint.y }
  }
}

// 水平梁动画：从外侧滑入
const getBeamHTransform = () => {
  switch (props.position) {
    case 'tl':
    case 'bl':
      return 'translateX(-40px)'
    case 'tr':
    case 'br':
      return 'translateX(40px)'
  }
}

// 垂直梁动画：从外侧滑入
const getBeamVTransform = () => {
  switch (props.position) {
    case 'tl':
    case 'tr':
      return 'translateY(-40px)'
    case 'bl':
    case 'br':
      return 'translateY(40px)'
  }
}

const joint = getJointXY()
const beamH = getBeamH()
const beamV = getBeamV()
</script>

<template>
  <div
    class="sunmao-ornament"
    :class="positionClasses[position]"
    :style="{
      width: `${size}px`,
      height: `${size}px`,
      '--animation-delay': `${animationDelay}ms`
    }"
  >
    <svg viewBox="0 0 100 100" class="sunmao-svg" preserveAspectRatio="xMidYMid meet">
      <!-- 水平梁 -->
      <rect
        class="sunmao-beam-h"
        :x="beamH.x"
        :y="beamH.y"
        :width="beamH.width"
        height="8"
      />
      <!-- 垂直梁 -->
      <rect
        class="sunmao-beam-v"
        :x="beamV.x"
        :y="beamV.y"
        :width="beamV.width"
        :height="beamV.height"
      />
      <!-- 连接点 -->
      <rect
        class="sunmao-joint"
        :x="joint.x"
        :y="joint.y"
        width="8"
        height="8"
      />
      <!-- 榫卯细节 -->
      <rect class="sunmao-tenon" :x="joint.x - 2" :y="joint.y + 2" width="2" height="4" />
      <rect class="sunmao-tenon" :x="joint.x + 8" :y="joint.y + 2" width="2" height="4" />
      <rect class="sunmao-tenon" :x="joint.x + 2" :y="joint.y - 2" width="4" height="2" />
      <rect class="sunmao-tenon" :x="joint.x + 2" :y="joint.y + 8" width="4" height="2" />
    </svg>
  </div>
</template>

<style scoped>
.sunmao-ornament {
  position: absolute;
  opacity: 0;
  animation: ornamentIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: var(--animation-delay, 0ms);
}

.sunmao-ornament.sunmao-tl {
  top: 8px;
  left: 8px;
}

.sunmao-ornament.sunmao-tr {
  top: 8px;
  right: 8px;
}

.sunmao-ornament.sunmao-bl {
  bottom: 8px;
  left: 8px;
}

.sunmao-ornament.sunmao-br {
  bottom: 8px;
  right: 8px;
}

@keyframes ornamentIn {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.sunmao-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.sunmao-beam-h {
  fill: rgba(139, 38, 53, 0.08);
  stroke: var(--color-seal, #8b2635);
  stroke-width: 1;
  opacity: 0;
  animation: beamSlideH 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: calc(var(--animation-delay, 0ms) + 200ms);
}

.sunmao-beam-v {
  fill: rgba(139, 38, 53, 0.06);
  stroke: var(--color-seal, #8b2635);
  stroke-width: 1;
  opacity: 0;
  animation: beamSlideV 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: calc(var(--animation-delay, 0ms) + 400ms);
}

.sunmao-joint {
  fill: var(--color-seal, #8b2635);
  opacity: 0;
  animation: jointLock 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: calc(var(--animation-delay, 0ms) + 700ms);
}

.sunmao-tenon {
  fill: var(--color-accent, #c9a96e);
  opacity: 0;
  animation: tenonPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: calc(var(--animation-delay, 0ms) + 900ms);
}

@keyframes beamSlideH {
  0% {
    opacity: 0;
    transform: v-bind('getBeamHTransform()');
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes beamSlideV {
  0% {
    opacity: 0;
    transform: v-bind('getBeamVTransform()');
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes jointLock {
  0% {
    opacity: 0;
    transform: scale(0);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes tenonPop {
  0% {
    opacity: 0;
    transform: scale(0);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
