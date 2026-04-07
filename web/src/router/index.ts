/**
 * 文件: web/src/router/index.ts
 * 说明: 应用路由配置与注册入口，负责页面映射、路由懒加载以及嵌套路由定义。
 *
 * 路由管线:
 *   - 初始化: 创建 Router 实例并注册所有路由定义（同步操作，O(1)）。
 *   - 懒加载: 路由组件使用动态 import 在首次访问时按需加载代码块，减少首屏体积。
 *   - 嵌套路由: 数据/页面分组通过子路由组织（例如 `/data` 下的 overview/download/storage）。
 *
 * 复杂度:
 *   - 路由匹配与导航为常数时间（由浏览器与 Vue Router 实现），懒加载决定网络请求开销。
 *
 * 关键点与风险:
 *   - 使用 `createWebHashHistory`（Hash 模式）避免服务端配置，但若需友好 URL 可切换为 `createWebHistory` 并配置服务器回退。
 *   - 懒加载 chunk 的命名与数量会影响 HTTP/2 下的小文件开销，建议合并或按需分组。
 *   - 未显式添加全局路由守卫、错误捕获或 404 页面，导航异常与权限控制需补充。
 */
import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/authors',
      name: 'authors',
      component: () => import('@/views/AuthorsView.vue')
    },
    {
      path: '/authors/clusters',
      name: 'author-clusters',
      redirect: '/authors'
    },
    {
      path: '/authors/clusters/:id',
      name: 'cluster-detail',
      component: () => import('@/views/ClusterDetailView.vue')
    },
    {
      path: '/authors/:name',
      name: 'author-detail',
      component: () => import('@/views/AuthorDetailView.vue')
    },
    {
      path: '/poems',
      name: 'poems',
      component: () => import('@/views/PoemsView.vue')
    },
    {
      path: '/poems/:id',
      name: 'poem-detail',
      component: () => import('@/views/PoemDetailView.vue')
    },
    {
      path: '/word-count',
      name: 'word-count',
      component: () => import('@/views/KeywordView.vue')
    },
    {
      path: '/keyword/:word',
      name: 'keyword-detail',
      component: () => import('@/views/KeywordDetailView.vue')
    },
    {
      path: '/word-sim',
      name: 'word-sim',
      redirect: '/word-count'
    },
    {
      path: '/data',
      name: 'data',
      component: () => import('@/views/DataView.vue'),
      children: [
        {
          path: '',
          redirect: '/data/overview'
        },
        {
          path: 'overview',
          name: 'data-overview',
          component: () => import('@/views/DataOverviewView.vue')
        },
        {
          path: 'download',
          name: 'data-download',
          component: () => import('@/views/DataDownloadView.vue')
        },
        {
          path: 'storage',
          name: 'data-storage',
          component: () => import('@/views/DataStorageView.vue')
        }
      ]
    },
  ]
})

export default router
