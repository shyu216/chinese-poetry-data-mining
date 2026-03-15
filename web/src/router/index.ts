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
      path: '/poems',
      name: 'poems',
      component: () => import('@/views/PoetsView.vue')
    },
    {
      path: '/poems/:id',
      name: 'poem-detail',
      component: () => import('@/views/PoemDetailView.vue')
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
      path: '/data',
      name: 'data',
      component: () => import('@/views/DataDashboardView.vue')
    },
    {
      path: '/stats',
      name: 'stats',
      component: () => import('@/views/StatsView.vue')
    },
    {
      path: '/wordcloud',
      name: 'wordcloud',
      component: () => import('@/views/WordcloudView.vue')
    }
  ]
})

export default router
