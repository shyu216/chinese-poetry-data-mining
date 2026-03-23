<script setup lang="ts">
interface Props {
  position: 'tl' | 'tr' | 'bl' | 'br'
  size?: number
  animationDelay?: number
}

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

const getBeamHX = () => {
  switch (props.position) {
    case 'tl':
    case 'bl':
      return { x: 0, width: 56 }
    case 'tr':
    case 'br':
      return { x: 44, width: 56 }
  }
}

const getBeamVY = () => {
  switch (props.position) {
    case 'tl':
    case 'tr':
      return { y: 0, height: 56 }
    case 'bl':
    case 'br':
      return { y: 44, height: 56 }
  }
}

const getJointXY = () => {
  switch (props.position) {
    case 'tl':
      return { x: 32, y: 32 }
    case 'tr':
      return { x: 60, y: 32 }
    case 'bl':
      return { x: 32, y: 60 }
    case 'br':
      return { x: 60, y: 60 }
  }
}

const beamH = getBeamHX()
const beamV = getBeamVY()
const joint = getJointXY()
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
      <rect
        class="sunmao-beam-h"
        :x="beamH.x"
        y="32"
        :width="beamH.width"
        height="8"
      />
      <rect
        class="sunmao-beam-v"
        x="32"
        :y="beamV.y"
        width="8"
        :height="beamV.height"
      />
      <rect
        class="sunmao-joint"
        :x="joint.x"
        :y="joint.y"
        width="8"
        height="8"
      />
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
