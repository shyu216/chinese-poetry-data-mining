/**
 * 文件: web/src/main.ts
 * 说明: 应用入口，负责创建 Vue 应用实例、注册全局插件（路由、UI 组件库）并挂载。
 *
 * 启动管线 (Startup pipeline):
 *   1. createApp(App) -> 创建根实例
 *   2. app.use(router) 注册路由系统（包含懒加载路由）
 *   3. app.use(naive) 注册 Naive UI 作为组件库
 *   4. app.mount('#app') 将应用挂载到 DOM
 *
 * 复杂度:
 *   - 启动为常数时间 O(1)（调用注册、挂载）；路由懒加载会在首次访问相应路由时发生额外网络请求。
 *   - 空间开销主要来自已注册插件与首次加载的页面代码块，按需加载能将长期驻留内存降到最小。
 *
 * 关键技术:
 *   - Vue 3 + Composition API、Vite 构建（假定使用）
 *   - Naive UI：即开即用的组件库
 *   - 路由懒加载：降低首屏体积
 *
 * 潜在问题:
 *   - 无 SSR/Hydration：不利于 SEO 与首屏性能敏感场景。
 *   - 全局插件注册顺序可能影响行为（例如需要在路由之前初始化的插件）。
 *   - 未处理应用级错误捕获（可添加全局 errorHandler 或 ErrorBoundary 机制）。
 */
import { createApp } from 'vue'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'
import './styles/design-system.css'

const app = createApp(App)

app.use(router)
app.use(naive)

app.mount('#app')
