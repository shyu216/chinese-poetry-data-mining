<!--
  @overview
  file: web/src/components/feedback/UnifiedLoading.vue
  category: frontend-component
  tech: Vue 3 + TypeScript
  solved: 统一的加载指示组件（全屏阻塞 / 浮动非阻塞），视觉风格收敛为单一进度环，
         颜色全部取自设计系统 token，深浅色主题自动适配，避免复杂水墨装饰带来的视觉疲劳。
  data_source: 组合式状态与组件内部状态（useLoading）
  data_flow: 状态输入 -> 组件渲染(Transition) + 进度环(基于 stroke-dashoffset)
  complexity: 初始化与轻量交互为主，进度动画用 requestAnimationFrame 平滑插值，典型 O(1)~O(n)
  unique: 关键函数: animate；主渲染组件: Transition + SVG progress ring
-->
<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useLoading } from '@/composables/useLoading'

const loading = useLoading()

// 状态
const state = loading.state
const isBlocking = loading.isBlocking
const isNonBlocking = loading.isNonBlocking
const progressPercent = loading.progressPercent

// 显示用的进度（平滑动画）
const displayProgress = ref(0)
const displayDescription = ref('')

// 平滑进度动画
watch(progressPercent, (newVal) => {
  const animate = () => {
    const diff = newVal - displayProgress.value
    if (Math.abs(diff) < 0.5) {
      displayProgress.value = newVal
    } else {
      displayProgress.value += diff * 0.15
      requestAnimationFrame(animate)
    }
  }
  animate()
}, { immediate: true })

// 描述文案
watch(() => state.description, (newDesc) => {
  if (newDesc) {
    displayDescription.value = newDesc
  }
}, { immediate: true })

// 格式化进度
const formattedProgress = computed(() => Math.round(displayProgress.value))

// 进度文本
const progressText = computed(() => {
  if (state.total > 0) {
    return `${state.current.toLocaleString()} / ${state.total.toLocaleString()}`
  }
  return `${formattedProgress.value}%`
})

// 是否有数值进度（决定是否显示确定进度环或不确定旋转环）
const hasNumericProgress = computed(() => state.total > 0)
const isComplete = computed(() => state.phase === 'complete')
const isError = computed(() => state.phase === 'error')
const isIndeterminate = computed(
  () => !hasNumericProgress.value && !isComplete.value && !isError.value
)

// 进度环几何
const RING_R = 54
const circumference = 2 * Math.PI * RING_R
const dashOffset = computed(() => circumference * (1 - displayProgress.value / 100))
</script>

<template>
  <div class="unified-loading">
    <!-- Blocking Loading: 全屏遮罩 + 单一进度环 -->
    <Transition name="overlay-fade">
      <div v-if="isBlocking" class="blocking-overlay">
        <div class="loading-panel">
          <div class="ring-wrap">
            <svg
              class="ring"
              :class="{ spinning: isIndeterminate }"
              viewBox="0 0 120 120"
            >
              <circle class="ring-track" cx="60" cy="60" :r="RING_R" />
              <circle
                class="ring-value"
                :class="{ indeterminate: isIndeterminate }"
                cx="60"
                cy="60"
                :r="RING_R"
                :stroke-dasharray="isIndeterminate ? `${circumference * 0.28} ${circumference}` : circumference"
                :stroke-dashoffset="isIndeterminate ? 0 : dashOffset"
              />
            </svg>
            <div class="ring-center">
              <span v-if="isComplete" class="state-icon complete">✓</span>
              <span v-else-if="isError" class="state-icon error">✕</span>
              <template v-else>
                <span class="progress-number">{{ formattedProgress }}</span>
                <span class="progress-unit">%</span>
              </template>
            </div>
          </div>

          <div class="loading-info">
            <h3 class="loading-title" :class="{ complete: isComplete, error: isError }">
              {{ state.title || '加载中' }}
            </h3>
            <p class="loading-description">
              {{ displayDescription || '请稍候…' }}
            </p>
            <div v-if="hasNumericProgress && !isComplete && !isError" class="loading-stats">
              <span class="stats-text">{{ progressText }}</span>
            </div>
            <div v-else-if="isIndeterminate" class="loading-dots" aria-hidden="true">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Non-blocking Loading: 浮动提示 -->
    <Transition name="float-slide">
      <div v-if="isNonBlocking" class="non-blocking-float">
        <div class="float-content">
          <div class="float-header">
            <span class="float-icon" :class="{ searching: state.phase === 'search' }">🔍</span>
            <span class="float-title">{{ state.title }}</span>
          </div>
          <div class="float-body">
            <div class="progress-info">
              <span class="description-text">{{ displayDescription }}</span>
              <span v-if="hasNumericProgress" class="count-badge">
                {{ state.current }} / {{ state.total }}
              </span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: `${displayProgress}%` }"></div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.unified-loading {
  pointer-events: none;
}

/* ========== Blocking Loading ========== */
.blocking-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--overlay-bg);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
  pointer-events: auto;
}

.loading-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-10) var(--space-12);
  width: calc(100% - 40px);
  max-width: 360px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  -webkit-backdrop-filter: blur(var(--glass-blur));
  backdrop-filter: blur(var(--glass-blur));
}

/* 进度环 */
.ring-wrap {
  position: relative;
  width: 120px;
  height: 120px;
}

.ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring.spinning {
  transform: rotate(0deg);
  animation: ringSpin 1s linear infinite;
}

.ring-track {
  fill: none;
  stroke: var(--ring-track);
  stroke-width: 6;
}

.ring-value {
  fill: none;
  stroke: var(--color-accent);
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 0 4px var(--color-accent-soft));
}

.ring-value.indeterminate {
  animation: ringPulse 1.6s ease-in-out infinite;
}

.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-number {
  font-family: var(--font-serif);
  font-size: 32px;
  font-weight: 600;
  color: var(--color-accent);
  line-height: 1;
}

.progress-unit {
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--color-secondary);
  opacity: 0.7;
  margin-left: 2px;
}

.state-icon {
  font-size: 40px;
  line-height: 1;
}

.state-icon.complete {
  color: var(--color-success);
  animation: checkPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.state-icon.error {
  color: var(--color-danger);
  animation: shake 0.4s ease-in-out;
}

/* 文字信息区 */
.loading-info {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  min-width: 240px;
}

.loading-title {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 2px;
  transition: color 0.3s ease;
}

.loading-title.complete {
  color: var(--color-success);
}

.loading-title.error {
  color: var(--color-danger);
}

.loading-description {
  margin: 0;
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--color-secondary);
  line-height: 1.6;
  min-height: 22px;
}

.loading-stats {
  margin-top: var(--space-1);
}

.stats-text {
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--color-accent);
  font-weight: 500;
  padding: 4px 12px;
  background: var(--color-accent-soft);
  border-radius: var(--radius-full);
}

/* 不确定状态：三点呼吸 */
.loading-dots {
  display: inline-flex;
  gap: 6px;
  margin-top: var(--space-1);
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-accent);
  animation: breathe 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

/* ========== Non-blocking Loading ========== */
.non-blocking-float {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1000;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  -webkit-backdrop-filter: blur(var(--glass-blur));
  backdrop-filter: blur(var(--glass-blur));
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--space-4) var(--space-5);
  min-width: 280px;
  max-width: 320px;
  pointer-events: auto;
}

.float-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.float-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.float-icon {
  font-size: 18px;
  transition: transform 0.3s ease;
}

.float-icon.searching {
  animation: breathe 2s ease-in-out infinite;
}

.float-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-accent);
  font-family: var(--font-serif);
}

.float-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  gap: var(--space-3);
}

.description-text {
  color: var(--color-secondary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.count-badge {
  background: var(--color-accent);
  color: var(--color-accent-contrast);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 500;
  animation: fadeIn 0.3s ease;
  flex-shrink: 0;
}

.progress-bar {
  height: 4px;
  background: var(--color-accent-soft);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

/* ========== 过渡动画 ========== */
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.4s var(--ease-out-expo);
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

.overlay-fade-enter-active .loading-panel,
.overlay-fade-leave-active .loading-panel {
  transition: transform 0.4s var(--ease-out-expo), opacity 0.4s var(--ease-out-expo);
}

.overlay-fade-enter-from .loading-panel,
.overlay-fade-leave-to .loading-panel {
  opacity: 0;
  transform: scale(0.96);
}

.float-slide-enter-active,
.float-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.float-slide-enter-from,
.float-slide-leave-to {
  opacity: 0;
  transform: translateX(100px);
}

/* ========== 关键帧 ========== */
@keyframes ringSpin {
  to { transform: rotate(360deg); }
}

@keyframes ringPulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}

@keyframes checkPop {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .loading-panel {
    padding: var(--space-8) var(--space-6);
  }

  .non-blocking-float {
    top: auto;
    bottom: 20px;
    right: 16px;
    left: 16px;
    min-width: auto;
    max-width: none;
  }
}
</style>
