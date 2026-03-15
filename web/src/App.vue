<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'

const collapsed = ref(false)
const themeOverrides = {
  common: {
    primaryColor: '#c41e3a',
    primaryColorHover: '#d63f52',
    primaryColorPressed: '#a01830'
  }
}
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-layout has-sider position="absolute" style="top: 0; bottom: 64px">
      <n-layout-sider
        bordered
        collapse-mode="width"
        :collapsed-width="64"
        :width="240"
        :collapsed="collapsed"
        show-trigger
        @collapse="collapsed = true"
        @expand="collapsed = false"
        :native-scrollbar="false"
        style="height: 100%"
      >
        <div class="logo" v-if="!collapsed">
          <h2>诗词数据</h2>
          <p>Chinese Poetry Mining</p>
        </div>
        <n-menu
          :collapsed="collapsed"
          :collapsed-width="64"
          :collapsed-icon-size="22"
          :options="menuOptions"
          value="home"
        />
      </n-layout-sider>

      <n-layout content-style="padding: 16px" :native-scrollbar="false">
        <RouterView />
      </n-layout>
    </n-layout>

    <n-layout-footer position="absolute" style="height: 64px; padding: 0 24px" bordered>
      <div class="footer-content">
        <span>© 2026 Chinese Poetry Data Mining</span>
        <span>数据总量: 332,509 首诗词</span>
      </div>
    </n-layout-footer>
  </n-config-provider>
</template>

<script lang="ts">
import { h } from 'vue'
import type { Component } from 'vue'
import { NIcon } from 'naive-ui'
import {
  BookOutline as BookIcon,
  SearchOutline as SearchIcon,
  PeopleOutline as PeopleIcon,
  BarChartOutline as StatsIcon,
  CloudOutline as CloudIcon
} from '@vicons/ionicons5'

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = [
  {
    label: () => h(RouterLink, { to: '/' }, { default: () => '首页搜索' }),
    key: 'home',
    icon: renderIcon(SearchIcon)
  },
  {
    label: () => h(RouterLink, { to: '/poems' }, { default: () => '诗词浏览' }),
    key: 'poems',
    icon: renderIcon(BookIcon)
  },
  {
    label: () => h(RouterLink, { to: '/authors' }, { default: () => '作者' }),
    key: 'authors',
    icon: renderIcon(PeopleIcon)
  },
  {
    label: () => h(RouterLink, { to: '/stats' }, { default: () => '统计' }),
    key: 'stats',
    icon: renderIcon(StatsIcon)
  },
  {
    label: () => h(RouterLink, { to: '/wordcloud' }, { default: () => '词云' }),
    key: 'wordcloud',
    icon: renderIcon(CloudIcon)
  }
]
</script>

<style scoped>
.logo {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid var(--n-border-color);
}

.logo h2 {
  margin: 0;
  color: #c41e3a;
  font-size: 18px;
}

.logo p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #666;
}

.footer-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: #666;
}

a {
  color: inherit;
  text-decoration: none;
}
</style>
