<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import {
  LibraryOutline as HomeIcon,
  BookOutline as PoemsIcon,
  PeopleOutline as AuthorsIcon,
  BarChartOutline as WordCountIcon,
  ServerOutline as DataIcon,
  MenuOutline,
  CloseOutline
} from '@vicons/ionicons5'

import { usePoemsV2 } from '@/composables/usePoemsV2'
import { UnifiedLoading } from '@/components/feedback'

const collapsed = ref(false)
const mobileMenuOpen = ref(false)
const isMobile = ref(false)
const isTransitioning = ref(false)

const poemsV2 = usePoemsV2()
const route = useRoute()

const formatNumber = (num: number | undefined | null): string => {
  if (num === undefined || num === null) return '--'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (!isMobile.value) {
    mobileMenuOpen.value = false
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  poemsV2.loadMetadata()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

const menuOptions = [
  { label: '启卷', key: 'home', path: '/', icon: HomeIcon },
  { label: '诗海', key: 'poems', path: '/poems', icon: PoemsIcon },
  { label: '墨客', key: 'authors', path: '/authors', icon: AuthorsIcon },
  { label: '词韵', key: 'word-count', path: '/word-count', icon: WordCountIcon },
  { label: '库藏', key: 'data', path: '/data', icon: DataIcon },
]

// 页面过渡动画配置
const getTransitionName = (route: RouteLocationNormalized) => {
  // 详情页使用水墨扩散效果
  if (route.path.includes('/poem/') || route.path.includes('/author/')) {
    return 'page-ink-spread'
  }
  // 列表页使用上滑效果
  if (route.path.includes('/poems') || route.path.includes('/authors')) {
    return 'page-slide-up'
  }
  // 默认淡入淡出
  return 'page-fade'
}

const onBeforeLeave = () => {
  isTransitioning.value = true
}

const onAfterEnter = () => {
  isTransitioning.value = false
}



const themeOverrides = {
  common: {
    primaryColor: '#8B2635',
    primaryColorHover: '#A83246',
    primaryColorPressed: '#6B1D27',
    primaryColorSuppl: '#8B2635',
    borderRadius: '3px',
    borderRadiusSmall: '2px',
    fontFamily: '"Noto Serif SC", "Source Han Serif SC", "Songti SC", serif',
    fontFamilyMono: '"Noto Sans SC", "PingFang SC", sans-serif'
  },
  Card: { borderRadius: '4px' },
  Button: { borderRadiusMedium: '3px', borderRadiusSmall: '2px' },
  Input: { borderRadius: '3px' },
  Tag: { borderRadius: '2px' }
}
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <div class="app-container">
          <!-- Mobile Header -->
          <header class="mobile-header" v-if="isMobile">
            <button class="menu-toggle" @click="mobileMenuOpen = !mobileMenuOpen">
              <MenuOutline v-if="!mobileMenuOpen" class="menu-icon" />
              <CloseOutline v-else class="menu-icon" />
            </button>
            <div class="mobile-brand">
              <RouterLink to="/" class="brand-seal" @click="mobileMenuOpen = false">诗词</RouterLink>
              <RouterLink to="/" class="mobile-title" @click="mobileMenuOpen = false">中华诗词库</RouterLink>
            </div>
          </header>

          <!-- Sidebar / Mobile Drawer -->
          <aside class="sidebar" :class="{ collapsed, 'mobile-open': mobileMenuOpen }">
            <div class="sidebar-header">
              <RouterLink to="/" class="brand" v-if="!collapsed">
                <span class="brand-seal">诗词</span>
                <div class="brand-text">
                  <h2>中华诗词库</h2>
                  <p>三十万首诗词数据挖掘</p>
                </div>
              </RouterLink>
              <RouterLink to="/" class="brand-mini" v-else>
                <span class="brand-seal">诗</span>
              </RouterLink>
            </div>

            <nav class="sidebar-nav">
              <RouterLink
                v-for="item in menuOptions"
                :key="item.key"
                :to="item.path"
                class="nav-item"
                :class="{ active: $route.path === item.path || ($route.path.startsWith(item.path + '/') && item.path !== '/') }"
                @click="isMobile && (mobileMenuOpen = false)"
              >
                <component :is="item.icon" class="nav-icon" />
                <span class="nav-label" v-if="!collapsed">{{ item.label }}</span>
              </RouterLink>
            </nav>

            <button v-if="!isMobile" class="collapse-btn" @click="collapsed = !collapsed">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path v-if="collapsed" d="M6 12l4-4-4-4v8z"/>
                <path v-else d="M10 4l-4 4 4 4V4z"/>
              </svg>
            </button>
          </aside>

          <!-- Mobile Overlay -->
          <div v-if="isMobile && mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>

          <main class="main-content">
            <RouterView v-slot="{ Component, route }">
              <transition 
                :name="getTransitionName(route)" 
                mode="out-in"
                @before-leave="onBeforeLeave"
                @after-enter="onAfterEnter"
              >
                <component :is="Component" :key="route.path" />
              </transition>
            </RouterView>
          </main>

          <footer class="app-footer">
            <div class="footer-inner">
              <span class="copyright">© 2026 中华诗词数据挖掘</span>
              <span class="divider">|</span>
              <span class="stats">收录诗词 <em>{{ formatNumber(poemsV2.totalPoems.value) }}</em> 首</span>
              <span class="divider">|</span>
              <span class="version">v1.0</span>
            </div>
          </footer>

          <!-- 统一加载组件 -->
          <UnifiedLoading />
        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500&display=swap');

:root {
  --color-bg: #FAF8F5;
  --color-bg-paper: #FDFCFA;
  --color-ink: #2C2416;
  --color-ink-light: #5C5244;
  --color-seal: #8B2635;
  --color-seal-light: #A83246;
  --color-border: #E8E4DD;
  --color-accent: #C9A96E;
  --shadow-subtle: 0 2px 8px rgba(44, 36, 22, 0.06);
  --shadow-card: 0 4px 16px rgba(44, 36, 22, 0.08);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--color-bg);
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  color: var(--color-ink);
  -webkit-font-smoothing: antialiased;
}

.app-container {
  display: flex;
  min-height: 100vh;
  background: 
    radial-gradient(ellipse at 20% 0%, rgba(139, 38, 53, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(201, 169, 110, 0.05) 0%, transparent 50%),
    var(--color-bg);
}

.sidebar {
  width: 260px;
  background: var(--color-bg-paper);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-subtle);
  z-index: 200;
}

.sidebar.collapsed { width: 72px; }

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid var(--color-border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  text-decoration: none;
  color: inherit;
  transition: opacity 0.2s ease;
}

.brand:hover {
  opacity: 0.85;
}

.brand-seal {
  width: 44px;
  height: 44px;
  background: var(--color-seal);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Noto Serif SC", serif;
  font-size: 20px;
  font-weight: 700;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(139, 38, 53, 0.3);
}

.brand-mini { display: flex; justify-content: center; }

.brand-mini:hover {
  opacity: 0.85;
}

.brand-mini .brand-seal {
  width: 36px;
  height: 36px;
  font-size: 16px;
}

.brand-text h2 {
  margin: 0;
  font-family: "Noto Serif SC", serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: 2px;
}

.brand-text p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-ink-light);
  letter-spacing: 1px;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 4px;
  color: var(--color-ink-light);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s ease;
  position: relative;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: var(--color-seal);
  border-radius: 0 2px 2px 0;
  transition: height 0.2s ease;
}

.nav-item:hover {
  background: rgba(139, 38, 53, 0.04);
  color: var(--color-ink);
}

.nav-item.active {
  background: rgba(139, 38, 53, 0.08);
  color: var(--color-seal);
  font-weight: 500;
}

.nav-item.active::before { height: 24px; }

.nav-icon {
  width: 20px;
  height: 20px;
  opacity: 0.8;
}

.nav-item.active .nav-icon { opacity: 1; }

.collapse-btn {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background: var(--color-bg-paper);
  border: 1px solid var(--color-border);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-light);
  transition: all 0.2s ease;
  z-index: 10;
}

.collapse-btn:hover {
  background: var(--color-seal);
  color: #fff;
  border-color: var(--color-seal);
}

.settings-btn {
  margin-top: auto;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-border);
  color: var(--color-ink-light);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.settings-btn:hover {
  background: rgba(139, 38, 53, 0.05);
  color: var(--color-seal);
}

.sidebar.collapsed .settings-btn {
  padding: 12px;
  justify-content: center;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: 260px;
  padding: 32px 40px;
  padding-bottom: 80px;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar.collapsed ~ .main-content {
  margin-left: 72px;
}

.app-footer {
  position: fixed;
  bottom: 0;
  left: 260px;
  right: 0;
  background: var(--color-bg-paper);
  border-top: 1px solid var(--color-border);
  padding: 0 40px;
  height: 56px;
  display: flex;
  align-items: center;
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
}

.sidebar.collapsed ~ .app-footer {
  left: 72px;
}

.footer-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: var(--color-ink-light);
}

.footer-inner .divider { opacity: 0.3; }

.footer-inner em {
  font-style: normal;
  color: var(--color-seal);
  font-weight: 600;
}

/* ========== 页面过渡动画 ========== */

/* 淡入淡出 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* 上滑入 */
.page-slide-up-enter-active,
.page-slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 水墨扩散 */
.page-ink-spread-enter-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-ink-spread-leave-active {
  transition: all 0.3s ease;
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

/* 旧版兼容 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from, .fade-leave-to { opacity: 0; }

a { color: inherit; text-decoration: none; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--color-accent); }

/* Mobile Styles */
@media (max-width: 768px) {
  .mobile-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 56px;
    background: var(--color-bg-paper);
    border-bottom: 1px solid var(--color-border);
    display: flex;
    align-items: center;
    padding: 0 16px;
    z-index: 300;
    gap: 12px;
  }

  .menu-toggle {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    color: var(--color-ink);
    cursor: pointer;
    border-radius: 4px;
  }

  .menu-toggle:hover {
    background: rgba(139, 38, 53, 0.08);
  }

  .menu-icon {
    width: 24px;
    height: 24px;
  }

  .mobile-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mobile-brand a {
  text-decoration: none;
  color: inherit;
}

.mobile-brand a:hover {
  opacity: 0.85;
}

  .mobile-brand .brand-seal {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }

  .mobile-title {
    font-family: "Noto Serif SC", serif;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-ink);
  }

  .sidebar {
    transform: translateX(-100%);
    width: 280px;
    top: 56px;
    height: calc(100vh - 56px);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .mobile-overlay {
    position: fixed;
    top: 56px;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 150;
  }

  .main-content {
    margin-left: 0 !important;
    margin-top: 56px;
    padding: 16px;
    padding-bottom: 80px;
    min-height: calc(100vh - 56px);
  }

  .app-footer {
    left: 0 !important;
    padding: 0 16px;
    height: 48px;
  }

  .footer-inner {
    font-size: 12px;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .footer-inner .divider {
    display: none;
  }

  .footer-inner span:not(.divider) {
    white-space: nowrap;
  }
}

/* Tablet Styles */
@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar {
    width: 220px;
  }

  .sidebar.collapsed {
    width: 64px;
  }

  .main-content {
    margin-left: 220px;
    padding: 24px 32px;
  }

  .sidebar.collapsed ~ .main-content {
    margin-left: 64px;
  }

  .app-footer {
    left: 220px;
    padding: 0 32px;
  }

  .sidebar.collapsed ~ .app-footer {
    left: 64px;
  }
}

/* Hide mobile elements on desktop */
@media (min-width: 769px) {
  .mobile-header,
  .mobile-overlay {
    display: none;
  }
}
</style>
