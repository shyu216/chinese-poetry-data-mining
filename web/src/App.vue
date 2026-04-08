<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import {
  HomeOutline,
  BookOutline,
  PeopleOutline,
  BarChartOutline,
  SettingsOutline,
  MenuOutline,
  CloseOutline,
  SearchOutline,
  ShareSocialOutline,
  PersonOutline
} from '@vicons/ionicons5'

import { usePoems } from '@/composables/usePoems'
import { UnifiedLoading } from '@/components/feedback'

const collapsed = ref(false)
const mobileMenuOpen = ref(false)
const isMobile = ref(false)
const isTablet = ref(false)
const isTransitioning = ref(false)
const scrolled = ref(false)

const poems = usePoems()
const route = useRoute()

const formatNumber = (num: number | undefined | null): string => {
  if (num === undefined || num === null) return '--'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}

const checkDevice = () => {
  const width = window.innerWidth
  isMobile.value = width < 768
  isTablet.value = width >= 768 && width < 1024
  if (!isMobile.value) {
    mobileMenuOpen.value = false
  }
}

const handleScroll = () => {
  scrolled.value = window.scrollY > 20
}

onMounted(() => {
  checkDevice()
  window.addEventListener('resize', checkDevice)
  window.addEventListener('scroll', handleScroll)
  poems.loadMetadata()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDevice)
  window.removeEventListener('scroll', handleScroll)
})

const menuItems = [
  { label: '首页', key: 'home', path: '/', icon: HomeOutline },
  { label: '诗词', key: 'poems', path: '/poems', icon: BookOutline },
  { label: '作者', key: 'authors', path: '/authors', icon: PeopleOutline },
  { label: '词频', key: 'word-count', path: '/word-count', icon: BarChartOutline },
  { label: '数据', key: 'data', path: '/data', icon: SettingsOutline },
]

const getTransitionName = (route: RouteLocationNormalized) => {
  if (route.path.includes('/poem/') || route.path.includes('/author/')) {
    return 'page-ink-spread'
  }
  if (route.path.includes('/poems') || route.path.includes('/authors')) {
    return 'page-slide-up'
  }
  return 'page-fade'
}

const onBeforeLeave = () => {
  isTransitioning.value = true
}

const onAfterEnter = () => {
  isTransitioning.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const themeOverrides = {
  common: {
    primaryColor: '#2D6A6A',
    primaryColorHover: '#3D8B7A',
    primaryColorPressed: '#1F4A4A',
    primaryColorSuppl: '#2D6A6A',
    borderRadius: '8px',
    borderRadiusSmall: '6px',
    fontFamily: '"Noto Sans SC", "PingFang SC", sans-serif',
    fontFamilyMono: '"SF Mono", "Fira Code", monospace'
  },
  Card: { borderRadius: '12px' },
  Button: { borderRadiusMedium: '8px', borderRadiusSmall: '6px' },
  Input: { borderRadius: '8px' },
  Tag: { borderRadius: '6px' }
}

const currentYear = new Date().getFullYear()
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <div class="app-container" :class="{ 'is-mobile': isMobile, 'is-scrolled': scrolled }">
          <!-- Top Navigation Bar -->
          <header class="top-nav" :class="{ 'nav-scrolled': scrolled }">
            <div class="nav-inner">
              <!-- Mobile Menu Toggle -->
              <button 
                v-if="isMobile" 
                class="nav-toggle"
                @click="mobileMenuOpen = !mobileMenuOpen"
                aria-label="菜单"
              >
                <MenuOutline v-if="!mobileMenuOpen" />
                <CloseOutline v-else />
              </button>

              <!-- Brand -->
              <RouterLink to="/" class="nav-brand" @click="mobileMenuOpen = false">
                <div class="brand-icon">
                  <span class="brand-char">诗</span>
                </div>
                <span class="brand-name hide-mobile">中华诗词库</span>
              </RouterLink>

              <!-- Desktop Navigation -->
              <nav class="nav-links hide-mobile">
                <RouterLink
                  v-for="item in menuItems"
                  :key="item.key"
                  :to="item.path"
                  class="nav-link"
                  :class="{ active: $route.path === item.path || ($route.path.startsWith(item.path + '/') && item.path !== '/') }"
                >
                  <component :is="item.icon" class="nav-link-icon" />
                  <span>{{ item.label }}</span>
                </RouterLink>
              </nav>

              <!-- GitHub Link -->
              <div class="nav-actions">
                <a 
                  href="https://github.com/shyu216/chinese-poetry-data-mining" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="github-link hide-mobile"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" class="github-icon">
                    <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
                  </svg>
                </a>
              </div>
            </div>
          </header>

          <!-- Mobile Navigation Drawer -->
          <transition name="drawer">
            <aside v-if="isMobile && mobileMenuOpen" class="mobile-drawer">
              <div class="drawer-header">
                <RouterLink to="/" class="drawer-brand" @click="mobileMenuOpen = false">
                  <div class="brand-icon">
                    <span class="brand-char">诗</span>
                  </div>
                  <span class="brand-name">中华诗词库</span>
                </RouterLink>
              </div>
              <nav class="drawer-nav">
                <RouterLink
                  v-for="item in menuItems"
                  :key="item.key"
                  :to="item.path"
                  class="drawer-link"
                  :class="{ active: $route.path === item.path }"
                  @click="mobileMenuOpen = false"
                >
                  <component :is="item.icon" class="drawer-link-icon" />
                  <span>{{ item.label }}</span>
                </RouterLink>
              </nav>
              <div class="drawer-footer">
                <p class="drawer-stats">
                  收录 <strong>{{ formatNumber(poems.totalPoems.value) }}</strong> 首诗词
                </p>
                <a 
                  href="https://github.com/shyu216/chinese-poetry-data-mining" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="drawer-github"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" class="github-icon">
                    <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
                  </svg>
                  <span>GitHub</span>
                </a>
              </div>
            </aside>
          </transition>

          <!-- Mobile Overlay -->
          <transition name="fade">
            <div 
              v-if="isMobile && mobileMenuOpen" 
              class="mobile-overlay" 
              @click="mobileMenuOpen = false"
            ></div>
          </transition>

          <!-- Main Content Area -->
          <main class="main-wrapper">
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

          <!-- Footer -->
          <footer class="site-footer">
            <div class="footer-inner">
              <div class="footer-brand">
                <div class="brand-icon small">
                  <span class="brand-char">诗</span>
                </div>
                <span>中华诗词数据挖掘</span>
              </div>
              <p class="footer-copy">
                © {{ currentYear }} Chinese Poetry Data Mining
              </p>
            </div>
          </footer>

          <UnifiedLoading />
        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;600&display=swap');

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-primary);
}

/* ═══════════════════════════════════════════════════════════════
   Top Navigation
══════════════════════════════════════════════════════════════ */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(250, 250, 248, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid transparent;
  transition: all 0.3s var(--ease-out-expo);
}

.top-nav.nav-scrolled {
  background: rgba(250, 250, 248, 0.95);
  border-bottom-color: var(--border-light);
  box-shadow: var(--shadow-sm);
}

.nav-inner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  max-width: var(--container-xl);
  margin: 0 auto;
  padding: var(--space-3) var(--space-4);
  height: 60px;
}

@media (min-width: 768px) {
  .nav-inner {
    padding: var(--space-3) var(--space-6);
  }
}

.nav-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--ink-dark);
  border-radius: var(--radius-md);
  transition: background 0.2s;
}

.nav-toggle:hover {
  background: var(--ink-fog);
}

.nav-toggle svg {
  width: 24px;
  height: 24px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
  color: var(--ink-dark);
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ink-dark);
  border-radius: var(--radius-md);
  transition: transform 0.3s var(--ease-out-expo);
}

.brand-icon.small {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
}

.brand-icon:hover {
  transform: scale(1.05);
}

.brand-char {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  color: var(--paper-white);
}

.brand-icon.small .brand-char {
  font-size: 12px;
}

.brand-name {
  font-family: var(--font-serif);
  font-size: var(--text-lg);
  font-weight: 600;
  letter-spacing: 0.05em;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-left: var(--space-8);
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--ink-medium);
  text-decoration: none;
  border-radius: var(--radius-lg);
  transition: all 0.2s var(--ease-out-quart);
}

.nav-link:hover {
  color: var(--ink-dark);
  background: var(--ink-fog);
}

.nav-link.active {
  color: var(--ink-dark);
  background: var(--ink-fog);
}

.nav-link-icon {
  width: 18px;
  height: 18px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.github-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  color: var(--ink-gray);
  text-decoration: none;
  border: none;
  border-radius: var(--radius-full);
  transition: all 0.2s;
}

.github-link:hover {
  color: var(--ink-dark);
  background: var(--ink-fog);
}

.github-icon {
  width: 24px;
  height: 24px;
}

/* ═══════════════════════════════════════════════════════════════
   Mobile Drawer
══════════════════════════════════════════════════════════════ */
.mobile-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--bg-primary);
  z-index: 200;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-float);
}

.drawer-header {
  padding: var(--space-6);
  border-bottom: var(--border-light);
}

.drawer-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
  color: var(--ink-dark);
}

.drawer-nav {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.drawer-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--ink-medium);
  text-decoration: none;
  border-radius: var(--radius-lg);
  transition: all 0.2s;
}

.drawer-link:hover,
.drawer-link.active {
  color: var(--ink-dark);
  background: var(--ink-fog);
}

.drawer-link-icon {
  width: 22px;
  height: 22px;
}

.drawer-footer {
  padding: var(--space-6);
  border-top: var(--border-light);
}

.drawer-stats {
  font-size: var(--text-sm);
  color: var(--ink-gray);
  margin: 0;
}

.drawer-stats strong {
  color: var(--accent-teal);
  font-weight: 600;
}

.drawer-github {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--ink-fog);
  border-radius: var(--radius-lg);
  color: var(--ink-medium);
  font-size: var(--text-sm);
  text-decoration: none;
  transition: all 0.2s;
}

.drawer-github:hover {
  background: var(--ink-mist);
  color: var(--ink-dark);
}

.drawer-github .github-icon {
  width: 18px;
  height: 18px;
}

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  z-index: 150;
}

/* ═══════════════════════════════════════════════════════════════
   Main Content
══════════════════════════════════════════════════════════════ */
.main-wrapper {
  flex: 1;
  padding-top: 60px;
  min-height: calc(100vh - 200px);
}

/* ═══════════════════════════════════════════════════════════════
   Footer
══════════════════════════════════════════════════════════════ */
.site-footer {
  margin-top: auto;
  padding: var(--space-12) var(--space-4);
  background: var(--bg-secondary);
  border-top: var(--border-light);
}

.footer-inner {
  max-width: var(--container-xl);
  margin: 0 auto;
  text-align: center;
}

.footer-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-serif);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--ink-dark);
  margin-bottom: var(--space-4);
}

.footer-stats {
  font-size: var(--text-sm);
  color: var(--ink-gray);
  margin: 0 0 var(--space-2);
}

.footer-copy {
  font-size: var(--text-xs);
  color: var(--ink-light);
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════════
   Page Transitions
══════════════════════════════════════════════════════════════ */
.page-fade-enter-active,
.page-fade-leave-active,
.page-ink-spread-enter-active,
.page-ink-spread-leave-active,
.page-slide-up-enter-active,
.page-slide-up-leave-active {
  transition: all 0.4s var(--ease-out-expo);
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

.page-ink-spread-enter-from {
  opacity: 0;
  transform: scale(0.96);
  filter: blur(4px);
}

.page-ink-spread-leave-to {
  opacity: 0;
  transform: scale(1.02);
  filter: blur(4px);
}

.page-slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-slide-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Drawer transitions */
.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.3s var(--ease-out-expo);
}

.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(-100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ═══════════════════════════════════════════════════════════════
   Responsive Utilities
══════════════════════════════════════════════════════════════ */
@media (max-width: 767px) {
  .hide-mobile {
    display: none !important;
  }
}

@media (min-width: 768px) {
  .hide-desktop {
    display: none !important;
  }
}
</style>
