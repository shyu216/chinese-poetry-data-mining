import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
      component: () => import('@/views/WordSimView.vue')
    },
    {
      path: '/data',
      name: 'data',
      component: () => import('@/views/DataDashboardView.vue')
    },
    {
      path: '/test',
      name: 'test',
      component: () => import('@/views/TestView.vue')
    },
    {
      path: '/components-demo',
      name: 'components-demo',
      component: () => import('@/views/ComponentDemoView.vue')
    }
  ]
})

export default router
