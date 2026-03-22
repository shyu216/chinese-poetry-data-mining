<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useLoading } from '@/composables/useLoading'

const loading = useLoading()

// 只显示阻塞性加载和骨架屏加载，后台加载不显示全屏遮罩
const isVisible = computed(() => {
  const task = loading.currentTask.value
  return loading.isLoading.value && task && (task.type === 'blocking' || task.type === 'skeleton')
})
const currentTask = computed(() => loading.currentTask.value)
const progress = computed(() => loading.progress.value)

// 是否有后台加载任务（用于显示轻量提示）
const hasBackgroundTask = computed(() => loading.isBackground.value)

const displayProgress = ref(0)
const displayDescription = ref('')

watch(progress, (newVal) => {
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

watch(() => currentTask.value?.description, (newDesc) => {
  if (newDesc) {
    displayDescription.value = newDesc
  }
}, { immediate: true })

const formattedProgress = computed(() => {
  return Math.round(displayProgress.value)
})

const hasNumericProgress = computed(() => {
  const task = currentTask.value
  return task && task.total !== undefined && task.current !== undefined
})

const progressText = computed(() => {
  const task = currentTask.value
  if (!task) return ''
  if (task.total && task.current !== undefined) {
    return `${task.current.toLocaleString()} / ${task.total.toLocaleString()}`
  }
  return `${formattedProgress.value}%`
})

const inkDropStyle = computed(() => ({
  transform: `scale(${0.8 + displayProgress.value / 500})`,
  opacity: 0.3 + (displayProgress.value / 200)
}))
</script>

<template>
  <Transition name="ink-fade">
    <div v-if="isVisible" class="global-loading-overlay">
      <!-- 水墨背景层 -->
      <div class="ink-background">
        <div class="ink-drop ink-drop-1" :style="inkDropStyle"></div>
        <div class="ink-drop ink-drop-2" :style="inkDropStyle"></div>
        <div class="ink-drop ink-drop-3"></div>
        <div class="paper-texture"></div>
      </div>

      <!-- 主内容区 -->
      <div class="loading-content">
        <!-- 书法笔触进度环 -->
        <div class="brush-ring-container">
          <svg class="brush-ring" viewBox="0 0 120 120">
            <!-- 背景圆环 -->
            <circle
              class="ring-bg"
              cx="60"
              cy="60"
              r="52"
              fill="none"
              stroke="rgba(139, 38, 53, 0.1)"
              stroke-width="2"
            />
            <!-- 进度圆环 -->
            <circle
              class="ring-progress"
              cx="60"
              cy="60"
              r="52"
              fill="none"
              stroke="#8B2635"
              stroke-width="3"
              stroke-linecap="round"
              :stroke-dasharray="`${326.73 * displayProgress / 100} 326.73`"
              transform="rotate(-90 60 60)"
            />
            <!-- 装饰墨点 -->
            <circle class="ink-dot ink-dot-1" cx="60" cy="8" r="3" fill="#8B2635" />
            <circle class="ink-dot ink-dot-2" cx="112" cy="60" r="2" fill="#C9A96E" />
            <circle class="ink-dot ink-dot-3" cx="60" cy="112" r="2.5" fill="#8B2635" />
          </svg>

          <!-- 中心文字 -->
          <div class="ring-center">
            <span class="progress-number">{{ formattedProgress }}</span>
            <span class="progress-unit">%</span>
          </div>
        </div>

        <!-- 文字信息区 -->
        <div class="loading-info">
          <h3 class="loading-title">
            {{ currentTask?.title || '加载中' }}
          </h3>
          <p class="loading-description" :class="{ 'has-content': displayDescription }">
            {{ displayDescription || '请稍候...' }}
          </p>
          <div v-if="hasNumericProgress" class="loading-stats">
            <span class="stats-text">{{ progressText }}</span>
          </div>
        </div>

        <!-- 底部呼吸线 -->
        <div class="breathing-line">
          <div class="line-progress" :style="{ width: `${displayProgress}%` }"></div>
        </div>
      </div>

      <!-- 四角装饰 -->
      <div class="corner-ornament corner-tl">
        <svg viewBox="0 0 40 40" class="corner-svg">
          <path d="M0,20 Q0,0 20,0" fill="none" stroke="#8B2635" stroke-width="1.5" opacity="0.4"/>
          <circle cx="8" cy="8" r="2" fill="#8B2635" opacity="0.3"/>
        </svg>
      </div>
      <div class="corner-ornament corner-tr">
        <svg viewBox="0 0 40 40" class="corner-svg">
          <path d="M40,20 Q40,0 20,0" fill="none" stroke="#8B2635" stroke-width="1.5" opacity="0.4"/>
          <circle cx="32" cy="8" r="2" fill="#8B2635" opacity="0.3"/>
        </svg>
      </div>
      <div class="corner-ornament corner-bl">
        <svg viewBox="0 0 40 40" class="corner-svg">
          <path d="M0,20 Q0,40 20,40" fill="none" stroke="#8B2635" stroke-width="1.5" opacity="0.4"/>
          <circle cx="8" cy="32" r="2" fill="#8B2635" opacity="0.3"/>
        </svg>
      </div>
      <div class="corner-ornament corner-br">
        <svg viewBox="0 0 40 40" class="corner-svg">
          <path d="M40,20 Q40,40 20,40" fill="none" stroke="#8B2635" stroke-width="1.5" opacity="0.4"/>
          <circle cx="32" cy="32" r="2" fill="#8B2635" opacity="0.3"/>
        </svg>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.global-loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(250, 248, 245, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* 水墨背景 */
.ink-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.ink-drop {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.ink-drop-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(139, 38, 53, 0.12) 0%, transparent 70%);
  top: 10%;
  left: 15%;
  animation: inkFloat1 8s ease-in-out infinite;
}

.ink-drop-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(201, 169, 110, 0.1) 0%, transparent 70%);
  bottom: 20%;
  right: 20%;
  animation: inkFloat2 10s ease-in-out infinite;
}

.ink-drop-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(44, 36, 22, 0.06) 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: inkPulse 4s ease-in-out infinite;
}

@keyframes inkFloat1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -20px) scale(1.1); }
}

@keyframes inkFloat2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-20px, 30px) scale(0.95); }
}

@keyframes inkPulse {
  0%, 100% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.5; transform: translate(-50%, -50%) scale(1.2); }
}

.paper-texture {
  position: absolute;
  inset: 0;
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(44, 36, 22, 0.015) 2px, rgba(44, 36, 22, 0.015) 4px),
    repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(44, 36, 22, 0.015) 2px, rgba(44, 36, 22, 0.015) 4px);
  opacity: 0.6;
}

/* 主内容区 */
.loading-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  padding: 48px 64px;
  background: rgba(253, 252, 250, 0.8);
  border: 1px solid rgba(139, 38, 53, 0.15);
  border-radius: 8px;
  box-shadow:
    0 8px 32px rgba(44, 36, 22, 0.08),
    0 2px 8px rgba(44, 36, 22, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

/* 书法笔触进度环 */
.brush-ring-container {
  position: relative;
  width: 140px;
  height: 140px;
}

.brush-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  stroke-dasharray: 4 4;
}

.ring-progress {
  transition: stroke-dasharray 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  filter: drop-shadow(0 0 4px rgba(139, 38, 53, 0.3));
}

.ink-dot {
  animation: dotPulse 2s ease-in-out infinite;
}

.ink-dot-1 { animation-delay: 0s; }
.ink-dot-2 { animation-delay: 0.3s; }
.ink-dot-3 { animation-delay: 0.6s; }

@keyframes dotPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.2); }
}

.ring-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.progress-number {
  font-family: "Noto Serif SC", serif;
  font-size: 36px;
  font-weight: 600;
  color: #8B2635;
  line-height: 1;
}

.progress-unit {
  font-family: "Noto Sans SC", sans-serif;
  font-size: 14px;
  color: #8B2635;
  opacity: 0.7;
}

/* 文字信息区 */
.loading-info {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 280px;
}

.loading-title {
  margin: 0;
  font-family: "Noto Serif SC", serif;
  font-size: 22px;
  font-weight: 600;
  color: #2C2416;
  letter-spacing: 4px;
}

.loading-description {
  margin: 0;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 14px;
  color: #5C5244;
  line-height: 1.6;
  min-height: 22px;
  transition: opacity 0.3s ease;
}

.loading-stats {
  margin-top: 4px;
}

.stats-text {
  font-family: "Noto Sans SC", sans-serif;
  font-size: 13px;
  color: #8B2635;
  font-weight: 500;
  padding: 4px 12px;
  background: rgba(139, 38, 53, 0.06);
  border-radius: 12px;
}

/* 底部呼吸线 */
.breathing-line {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(139, 38, 53, 0.08);
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

.line-progress {
  height: 100%;
  background: linear-gradient(90deg, #8B2635 0%, #A83246 50%, #8B2635 100%);
  background-size: 200% 100%;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: shimmer 2s linear infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 四角装饰 */
.corner-ornament {
  position: absolute;
  width: 40px;
  height: 40px;
  pointer-events: none;
}

.corner-tl { top: 24px; left: 24px; }
.corner-tr { top: 24px; right: 24px; }
.corner-bl { bottom: 24px; left: 24px; }
.corner-br { bottom: 24px; right: 24px; }

.corner-svg {
  width: 100%;
  height: 100%;
}

/* 过渡动画 */
.ink-fade-enter-active,
.ink-fade-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.ink-fade-enter-from,
.ink-fade-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

.ink-fade-enter-active .loading-content,
.ink-fade-leave-active .loading-content {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.ink-fade-enter-from .loading-content,
.ink-fade-leave-to .loading-content {
  opacity: 0;
  transform: translateY(20px);
}

/* 响应式 */
@media (max-width: 768px) {
  .loading-content {
    padding: 36px 40px;
    margin: 20px;
    min-width: auto;
    width: calc(100% - 40px);
    max-width: 360px;
  }

  .brush-ring-container {
    width: 120px;
    height: 120px;
  }

  .progress-number {
    font-size: 30px;
  }

  .loading-title {
    font-size: 18px;
    letter-spacing: 2px;
  }

  .loading-info {
    min-width: auto;
    width: 100%;
  }

  .corner-ornament {
    width: 30px;
    height: 30px;
  }

  .corner-tl { top: 16px; left: 16px; }
  .corner-tr { top: 16px; right: 16px; }
  .corner-bl { bottom: 16px; left: 16px; }
  .corner-br { bottom: 16px; right: 16px; }
}
</style>
