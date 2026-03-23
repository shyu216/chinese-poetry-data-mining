import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import importToCDN from 'vite-plugin-cdn-import'

export default defineConfig({
  plugins: [
    vue(),
    importToCDN({
      modules: [
        {
          name: 'vue',
          var: 'Vue',
          path: 'https://cdn.jsdelivr.net/npm/vue@3.5.29/dist/vue.global.min.js'
        },
        {
          name: 'vue-router',
          var: 'VueRouter',
          path: 'https://cdn.jsdelivr.net/npm/vue-router@4.6.4/dist/vue-router.global.min.js'
        },
        {
          name: 'naive-ui',
          var: 'naive',
          path: 'https://cdn.jsdelivr.net/npm/naive-ui@2.44.1/dist/index.min.js'
        },
        {
          name: '@vueuse/core',
          var: 'VueUse',
          path: 'https://cdn.jsdelivr.net/npm/@vueuse/core@14.2.1/index.iife.min.js'
        },
        {
          name: 'd3',
          var: 'd3',
          path: 'https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js'
        },
        {
          name: 'echarts',
          var: 'echarts',
          path: 'https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js'
        }
      ]
    })
  ],
  base: '/chinese-poetry-data-mining/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    warmup: {
      clientFiles: [
        './src/main.ts',
        './src/App.vue',
        './src/router/index.ts'
      ]
    }
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'naive-ui',
      '@vicons/ionicons5',
      'echarts'
    ]
  },
  build: {
    rollupOptions: {
      external: ['vue', 'vue-router', 'naive-ui', '@vueuse/core', 'd3', 'echarts'],
      output: {
        globals: {
          vue: 'Vue',
          'vue-router': 'VueRouter',
          'naive-ui': 'naive',
          '@vueuse/core': 'VueUse',
          d3: 'd3',
          echarts: 'echarts'
        }
      }
    }
  }
})
