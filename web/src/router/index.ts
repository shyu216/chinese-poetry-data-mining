/**
 * @overview
 * file: web/src/router/index.ts
 * category: router
 * tech: TypeScript + Vue Router
 * solved: 路由注册、页面映射与懒加载调度
 * data_source: 组合式状态与组件内部状态
 * data_flow: 状态输入 -> 组件渲染(UI 组件)
 * complexity: 初始化与轻量交互为主，典型场景近似 O(1)~O(n)
 * unique: 路径特征: web/src/router/index.ts
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
      component: () => import('@/views/WordCountView.vue')
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
