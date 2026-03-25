/**
 * @overview
 * file: web/src/main.ts
 * category: entry
 * tech: Vue 3 + TypeScript + Naive UI
 * solved: 应用启动入口：创建应用并挂载路由/全局能力
 * data_source: 组合式状态与组件内部状态
 * data_flow: 状态输入 -> 组件渲染(UI 组件)
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 路径特征: web/src/main.ts
 */
import { createApp } from 'vue'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)
app.use(naive)

app.mount('#app')
