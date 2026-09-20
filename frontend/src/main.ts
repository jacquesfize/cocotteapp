import '@fontsource-variable/inter'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { registerSW } from 'virtual:pwa-register'
import App from './App.vue'
import './assets/base.css'
import { i18n } from './i18n'
import { flushQueue, setupAutoSync } from './offline/sync'
import router from './router'
import { useAuthStore } from './stores/auth'
import { applyTheme } from './utils/theme'

document.documentElement.setAttribute('lang', i18n.global.locale.value)
applyTheme()

registerSW({ immediate: true })

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)

const authStore = useAuthStore()
if (authStore.isAuthenticated) {
  authStore.fetchMe().catch(() => {})
}

// Si des actions (ex. cocher un article de liste de courses) sont restées en attente
// d'une session précédente coupée hors ligne, on les rejoue dès que le réseau est là.
setupAutoSync()
flushQueue().catch(() => {})

app.mount('#app')
