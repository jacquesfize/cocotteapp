<script setup>
import { useRouter } from 'vue-router'
import { i18n, setLocale, SUPPORTED_LOCALES } from '../i18n'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}

function handleLocaleChange(event) {
  setLocale(event.target.value)
}
</script>

<template>
  <header class="navbar">
    <div class="container navbar-inner">
      <RouterLink to="/recipes" class="brand">{{ $t('app.title') }}</RouterLink>
      <div class="nav-actions">
        <nav v-if="authStore.isAuthenticated" class="links">
          <RouterLink to="/recipes">{{ $t('nav.recipes') }}</RouterLink>
          <RouterLink to="/planning">{{ $t('nav.planning') }}</RouterLink>
          <RouterLink to="/shopping-lists">{{ $t('nav.shopping') }}</RouterLink>
          <span class="muted">{{ authStore.user?.username }}</span>
          <button class="secondary" @click="handleLogout">{{ $t('nav.logout') }}</button>
        </nav>
        <nav v-else class="links">
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
    flex-direction: column;
    align-items: stretch;
    gap: 0.6rem;
  }

  .nav-actions {
    justify-content: space-between;
    gap: 0.6rem;
  }

  .links {
    gap: 0.6rem;
    font-size: 0.9rem;
  }

  .links button {
    padding: 0.4rem 0.7rem;
    min-height: auto;
  }
}
</style>
