import '@fontsource-variable/inter'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import './assets/base.css'
import { i18n } from './i18n'
import router from './router'
import { useAuthStore } from './stores/auth'

document.documentElement.setAttribute('lang', i18n.global.locale.value)

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)

const authStore = useAuthStore()
if (authStore.isAuthenticated) {
  authStore.fetchMe().catch(() => {})
}

app.mount('#app')
