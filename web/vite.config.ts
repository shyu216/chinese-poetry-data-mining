import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [
    vue(),
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
  }
})
