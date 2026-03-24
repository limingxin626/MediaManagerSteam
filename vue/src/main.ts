import { createApp } from 'vue'
import { API_BASE_URL } from './utils/constants'
import './style.css'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
