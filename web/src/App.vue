<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import {
  SearchOutline as SearchIcon,
  BookOutline as BookIcon,
  PeopleOutline as PeopleIcon,
  BarChartOutline as StatsIcon,
  CloudOutline as CloudIcon,
  SettingsOutline as SettingsIcon
} from '@vicons/ionicons5'
import SettingsPanel from '@/components/SettingsPanel.vue'

const collapsed = ref(false)
const showSettings = ref(false)

const menuOptions = [
  { label: '寻幽探微', key: 'home', path: '/', icon: SearchIcon },
  { label: '翰墨集珍', key: 'poems', path: '/poems', icon: BookIcon },
  { label: '文人雅士', key: 'authors', path: '/authors', icon: PeopleIcon },
  { label: '数据经纬', key: 'stats', path: '/stats', icon: StatsIcon },
  { label: '词林万象', key: 'wordcloud', path: '/wordcloud', icon: CloudIcon }
]

const footerLeft = computed(() => collapsed.value ? '72px' : '260px')

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
          <aside class="sidebar" :class="{ collapsed }">
            <div class="sidebar-header">
              <div class="brand" v-if="!collapsed">
                <span class="brand-seal">诗词</span>
                <div class="brand-text">
                  <h2>中华诗词库</h2>
                  <p>三十万首诗词数据挖掘</p>
                </div>
              </div>
              <div class="brand-mini" v-else>
                <span class="brand-seal">诗</span>
              </div>
            </div>
            
            <nav class="sidebar-nav">
              <RouterLink 
                v-for="item in menuOptions" 
                :key="item.key"
                :to="item.path"
                class="nav-item"
                :class="{ active: $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/') }"
              >
                <component :is="item.icon" class="nav-icon" />
                <span class="nav-label" v-if="!collapsed">{{ item.label }}</span>
              </RouterLink>
            </nav>

            <button class="collapse-btn" @click="collapsed = !collapsed">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path v-if="collapsed" d="M6 12l4-4-4-4v8z"/>
                <path v-else d="M10 4l-4 4 4 4V4z"/>
              </svg>
            </button>

            <button class="settings-btn" @click="showSettings = true" :title="collapsed ? '数据管理' : ''">
              <SettingsIcon class="nav-icon" />
              <span class="nav-label" v-if="!collapsed">数据管理</span>
            </button>
          </aside>

          <SettingsPanel v-model:show="showSettings" />

          <main class="main-content">
            <RouterView v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </RouterView>
          </main>

          <footer class="app-footer" :style="{ left: footerLeft }">
            <div class="footer-inner">
              <span class="copyright">© 2026 中华诗词数据挖掘</span>
              <span class="divider">|</span>
              <span class="stats">收录诗词 <em>332,712</em> 首</span>
              <span class="divider">|</span>
              <span class="version">v1.0</span>
            </div>
          </footer>
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
  position: relative;
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
  padding: 32px 40px;
  padding-bottom: 80px;
}

.app-footer {
  position: fixed;
  bottom: 0;
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
</style>
