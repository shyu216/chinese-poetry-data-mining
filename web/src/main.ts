import { createApp } from 'vue'
import { createNaiveUi } from 'naive-ui'
import App from './App.vue'
import router from './router'

const naive = createNaiveUi()

const app = createApp(App)

app.use(router)
app.use(naive)

app.mount('#app')
