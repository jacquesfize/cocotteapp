<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { i18n, setLocale, SUPPORTED_LOCALES } from '../i18n'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()

const isMenuOpen = ref(false)
const navbarEl = ref(null)

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function closeMenu() {
  isMenuOpen.value = false
}

function handleLogout() {
  closeMenu()
  authStore.logout()
  router.push({ name: 'login' })
}

function handleLocaleChange(event) {
  setLocale(event.target.value)
  closeMenu()
}

function handleOutsideClick(event) {
  if (isMenuOpen.value && navbarEl.value && !navbarEl.value.contains(event.target)) {
    closeMenu()
  }
}

function handleKeydown(event) {
  if (event.key === 'Escape') closeMenu()
}

const stopRouterWatch = router.afterEach(() => closeMenu())

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
  document.removeEventListener('keydown', handleKeydown)
  stopRouterWatch()
})
</script>

<template>
  <header ref="navbarEl" class="navbar">
    <div class="container navbar-inner">
      <RouterLink to="/recipes" class="brand" @click="closeMenu">{{ $t('app.title') }}</RouterLink>

      <button
        class="burger"
        type="button"
        :aria-expanded="isMenuOpen"
        aria-controls="nav-panel"
        :aria-label="t('nav.menu')"
        @click="toggleMenu"
      >
        <span class="burger-bar" />
        <span class="burger-bar" />
        <span class="burger-bar" />
      </button>

      <div id="nav-panel" class="nav-actions" :class="{ 'is-open': isMenuOpen }">
        <nav v-if="authStore.isAuthenticated" class="links" @click="closeMenu">
          <RouterLink to="/recipes">{{ $t('nav.recipes') }}</RouterLink>
          <RouterLink to="/planning">{{ $t('nav.planning') }}</RouterLink>
          <RouterLink to="/shopping-lists">{{ $t('nav.shopping') }}</RouterLink>
          <span class="muted">{{ authStore.user?.username }}</span>
          <button class="secondary" @click="handleLogout">{{ $t('nav.logout') }}</button>
        </nav>
        <nav v-else class="links" @click="closeMenu">
          <RouterLink to="/login">{{ $t('nav.login') }}</RouterLink>
          <RouterLink to="/register">{{ $t('nav.register') }}</RouterLink>
        </nav>
        <select class="locale-select" :value="i18n.global.locale.value" @change="handleLocaleChange">
          <option v-for="locale in SUPPORTED_LOCALES" :key="locale.code" :value="locale.code">
            {{ locale.label }}
          </option>
        </select>
      </div>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.navbar-inner {
  position: relative;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.brand {
  font-weight: 700;
  text-decoration: none;
  color: var(--color-text);
  white-space: nowrap;
}

.burger {
  display: none;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.links {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.links a {
  text-decoration: none;
}

.links a.router-link-active {
  font-weight: 600;
}

.locale-select {
  padding: 0.35rem 0.5rem;
  min-height: auto;
}

@media (max-width: 600px) {
  .navbar-inner {
    flex-wrap: nowrap;
  }

  .burger {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    width: 2.5rem;
    height: 2.5rem;
    padding: 0;
    background: transparent;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    flex-shrink: 0;
  }

  .burger-bar {
    display: block;
    width: 18px;
    height: 2px;
    border-radius: 2px;
    background: var(--color-text);
  }

  .nav-actions {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
    padding: 1rem;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
  }

  .nav-actions.is-open {
    display: flex;
  }

  .links {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }

  .locale-select {
    align-self: flex-start;
  }
}
</style>
