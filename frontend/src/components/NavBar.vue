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
const accountEl = ref(null)

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
  if (isMenuOpen.value && accountEl.value && !accountEl.value.contains(event.target)) {
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
  <header class="navbar">
    <div class="container navbar-inner">
      <RouterLink to="/" class="brand">
        <span class="brand-badge">
          <svg viewBox="0 0 100 100" fill="none">
            <path d="M40,22 C37,17 42,14 39,8" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity="0.85" />
            <path d="M58,22 C55,17 60,14 57,8" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity="0.85" />
            <rect x="8" y="50" width="12" height="9" rx="4.5" fill="#fff" />
            <rect x="80" y="50" width="12" height="9" rx="4.5" fill="#fff" />
            <path
              d="M22,48 C22,42 27,38 34,38 L66,38 C73,38 78,42 78,48 L78,66 C78,75 66,82 50,82 C34,82 22,75 22,66 Z"
              fill="#fff"
            />
            <rect x="16" y="33" width="68" height="9" rx="4.5" fill="#fff" />
            <circle cx="50" cy="28" r="6" fill="#fff" />
          </svg>
        </span>
        <span class="brand-name">{{ $t('app.title') }}</span>
      </RouterLink>

      <nav class="top-links">
        <RouterLink to="/">{{ $t('nav.home') }}</RouterLink>
        <RouterLink to="/recipes">{{ $t('nav.recipes') }}</RouterLink>
        <RouterLink to="/recipes/random">{{ $t('nav.random') }}</RouterLink>
        <template v-if="authStore.isAuthenticated">
          <RouterLink to="/planning">{{ $t('nav.planning') }}</RouterLink>
          <RouterLink to="/shopping-lists">{{ $t('nav.shopping') }}</RouterLink>
          <RouterLink v-if="authStore.user?.is_staff" to="/admin/users">{{ $t('nav.admin') }}</RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/login">{{ $t('nav.login') }}</RouterLink>
          <RouterLink to="/register">{{ $t('nav.register') }}</RouterLink>
        </template>
      </nav>

      <div ref="accountEl" class="account">
        <button
          class="account-button"
          type="button"
          :aria-expanded="isMenuOpen"
          aria-controls="account-panel"
          :aria-label="t('nav.account')"
          @click="toggleMenu"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <circle cx="12" cy="8.5" r="3.5" />
            <path d="M4.5 20c1.5-4 5-5.5 7.5-5.5s6 1.5 7.5 5.5" />
          </svg>
        </button>

        <div id="account-panel" class="account-panel" :class="{ 'is-open': isMenuOpen }">
          <p v-if="authStore.user" class="account-username">{{ authStore.user.username }}</p>
          <RouterLink v-if="authStore.isAuthenticated" to="/account" class="account-link" @click="closeMenu">
            {{ $t('nav.accountSettings') }}
          </RouterLink>
          <select class="locale-select" :value="i18n.global.locale.value" @change="handleLocaleChange">
            <option v-for="locale in SUPPORTED_LOCALES" :key="locale.code" :value="locale.code">
              {{ locale.label }}
            </option>
          </select>
          <button v-if="authStore.isAuthenticated" class="secondary" @click="handleLogout">
            {{ $t('nav.logout') }}
          </button>
        </div>
      </div>
    </div>
  </header>

  <nav class="tabbar" :aria-label="t('nav.menu')">
    <RouterLink to="/" class="tab-item">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 11.5 12 4l8 7.5" />
        <path d="M6 10v9h12v-9" />
      </svg>
      <span>{{ $t('nav.home') }}</span>
    </RouterLink>
    <RouterLink to="/recipes" class="tab-item">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 5.5c2-1 4.5-1 6.5 0v13c-2-1-4.5-1-6.5 0v-13Z" />
        <path d="M20 5.5c-2-1-4.5-1-6.5 0v13c2-1 4.5-1 6.5 0v-13Z" />
      </svg>
      <span>{{ $t('nav.recipes') }}</span>
    </RouterLink>
    <RouterLink to="/recipes/random" class="tab-item">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="4" />
        <circle cx="9" cy="9" r="1" fill="currentColor" stroke="none" />
        <circle cx="15" cy="15" r="1" fill="currentColor" stroke="none" />
        <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
      </svg>
      <span>{{ $t('nav.random') }}</span>
    </RouterLink>
    <template v-if="authStore.isAuthenticated">
      <RouterLink to="/planning" class="tab-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="5.5" width="16" height="15" rx="3" />
          <path d="M4 10h16" />
          <path d="M8 3.5v3M16 3.5v3" />
        </svg>
        <span>{{ $t('nav.planning') }}</span>
      </RouterLink>
      <RouterLink to="/shopping-lists" class="tab-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3.5 4.5h2l2.2 11a2 2 0 0 0 2 1.6h7.1a2 2 0 0 0 2-1.6l1.3-6.9H6.2" />
          <circle cx="10" cy="20" r="1.3" fill="currentColor" stroke="none" />
          <circle cx="17" cy="20" r="1.3" fill="currentColor" stroke="none" />
        </svg>
        <span>{{ $t('nav.shopping') }}</span>
      </RouterLink>
    </template>
  </nav>
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
  gap: 1rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 800;
  text-decoration: none;
  color: var(--color-text);
  white-space: nowrap;
}

.brand-badge {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 8px;
  background: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-badge svg {
  width: 65%;
  height: 65%;
}

.top-links {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex: 1;
  justify-content: center;
}

.top-links a {
  text-decoration: none;
  color: var(--color-text);
  font-weight: 600;
}

.top-links a.router-link-active {
  color: var(--color-primary);
}

.account {
  position: relative;
  flex-shrink: 0;
}

.account-button {
  background: var(--color-surface-muted);
  color: var(--color-text);
  border-radius: 999px;
  width: 2.75rem;
  height: 2.75rem;
  min-height: auto;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.account-button svg {
  width: 20px;
  height: 20px;
}

.account-button:hover {
  background: var(--color-primary-soft);
}

.account-panel {
  display: none;
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 200px;
  background: var(--color-surface);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  padding: 1rem;
  flex-direction: column;
  gap: 0.75rem;
  z-index: 30;
}

.account-panel.is-open {
  display: flex;
}

.account-username {
  margin: 0;
  font-weight: 700;
}

.account-link {
  color: var(--color-primary-dark);
  font-weight: 600;
  text-decoration: none;
  font-size: 0.9rem;
}

.locale-select {
  min-height: auto;
  padding: 0.4rem 0.6rem;
}

.tabbar {
  display: none;
}

@media (max-width: 600px) {
  .top-links {
    display: none;
  }

  .tabbar {
    display: flex;
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 20;
    background: var(--color-surface);
    border-top: 1px solid var(--color-border);
    padding: 0.4rem 0.5rem calc(0.4rem + env(safe-area-inset-bottom, 0px));
    justify-content: space-around;
  }

  .tab-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    text-decoration: none;
    color: var(--color-muted);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.3rem 0.5rem;
    border-radius: 12px;
    flex: 1;
  }

  .tab-item svg {
    width: 22px;
    height: 22px;
  }

  .tab-item.router-link-active {
    color: var(--color-primary);
  }
}
</style>
