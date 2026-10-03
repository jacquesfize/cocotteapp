<script setup lang="ts">
import { Check, Moon, Sun } from '@lucide/vue'
import { computed, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useClickOutside } from '../../composables/useClickOutside'
import { i18n, setLocale, SUPPORTED_LOCALES, type Locale } from '../../i18n'
import { useAuthStore } from '../../stores/auth'
import { themeMode, toggleThemeMode } from '../../utils/theme'
import LocaleFlag from './LocaleFlag.vue'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()

const isMenuOpen = ref(false)
const accountEl = ref<HTMLElement | null>(null)
const isLocaleMenuOpen = ref(false)
const localeEl = ref<HTMLElement | null>(null)
const currentLocaleLabel = computed(
  () => SUPPORTED_LOCALES.find((l) => l.code === i18n.global.locale.value)?.label ?? '',
)

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function closeMenu() {
  isMenuOpen.value = false
  isLocaleMenuOpen.value = false
}

function toggleLocaleMenu() {
  isLocaleMenuOpen.value = !isLocaleMenuOpen.value
}

function handleLogout() {
  closeMenu()
  authStore.logout()
  router.push({ name: 'login' })
}

function handleLocaleChange(code: Locale) {
  setLocale(code)
  closeMenu()
}

useClickOutside(accountEl, () => {
  isMenuOpen.value = false
})
useClickOutside(localeEl, () => {
  isLocaleMenuOpen.value = false
})

const stopRouterWatch = router.afterEach(() => closeMenu())

onBeforeUnmount(() => {
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
        <RouterLink to="/">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 11.5 12 4l8 7.5" />
            <path d="M6 10v9h12v-9" />
          </svg>
          <span>{{ $t('nav.home') }}</span>
        </RouterLink>
        <RouterLink to="/recipes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 5.5c2-1 4.5-1 6.5 0v13c-2-1-4.5-1-6.5 0v-13Z" />
            <path d="M20 5.5c-2-1-4.5-1-6.5 0v13c2-1 4.5-1 6.5 0v-13Z" />
          </svg>
          <span>{{ $t('nav.recipes') }}</span>
        </RouterLink>
        <template v-if="authStore.isAuthenticated">
          <RouterLink to="/planning">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="4" y="5.5" width="16" height="15" rx="3" />
              <path d="M4 10h16" />
              <path d="M8 3.5v3M16 3.5v3" />
            </svg>
            <span>{{ $t('nav.planning') }}</span>
          </RouterLink>
          <RouterLink to="/shopping-lists">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3.5 4.5h2l2.2 11a2 2 0 0 0 2 1.6h7.1a2 2 0 0 0 2-1.6l1.3-6.9H6.2" />
              <circle cx="10" cy="20" r="1.3" fill="currentColor" stroke="none" />
              <circle cx="17" cy="20" r="1.3" fill="currentColor" stroke="none" />
            </svg>
            <span>{{ $t('nav.shopping') }}</span>
          </RouterLink>
        </template>
      </nav>

      <div class="nav-actions">
        <RouterLink to="/recipes/random" class="dice-button" :aria-label="t('nav.random')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="4" />
            <circle cx="9" cy="9" r="1" fill="currentColor" stroke="none" />
            <circle cx="15" cy="15" r="1" fill="currentColor" stroke="none" />
            <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
          </svg>
        </RouterLink>

        <div ref="localeEl" class="locale">
          <button
            class="locale-button"
            type="button"
            data-testid="locale-button"
            :aria-expanded="isLocaleMenuOpen"
            aria-controls="locale-panel"
            :aria-label="t('nav.language', { name: currentLocaleLabel })"
            :title="currentLocaleLabel"
            @click="toggleLocaleMenu"
          >
            <LocaleFlag :code="i18n.global.locale.value" class="locale-flag" />
          </button>
          <div id="locale-panel" class="dropdown-panel locale-panel" :class="{ 'is-open': isLocaleMenuOpen }">
            <button
              v-for="locale in SUPPORTED_LOCALES"
              :key="locale.code"
              type="button"
              class="locale-option"
              :aria-pressed="locale.code === i18n.global.locale.value"
              @click="handleLocaleChange(locale.code)"
            >
              <LocaleFlag :code="locale.code" class="locale-option-flag" />
              <span class="locale-option-label">{{ locale.label }}</span>
              <Check v-if="locale.code === i18n.global.locale.value" :size="16" />
            </button>
          </div>
        </div>

        <button
          class="theme-toggle"
          type="button"
          data-testid="theme-toggle"
          :aria-label="themeMode === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')"
          @click="toggleThemeMode"
        >
          <Sun v-if="themeMode === 'dark'" :size="20" />
          <Moon v-else :size="20" />
        </button>

        <RouterLink
          v-if="!authStore.isAuthenticated"
          to="/login"
          class="account-button"
          data-testid="login-button"
          :aria-label="t('nav.login')"
          :title="t('nav.login')"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <circle cx="12" cy="8.5" r="3.5" />
            <path d="M4.5 20c1.5-4 5-5.5 7.5-5.5s6 1.5 7.5 5.5" />
          </svg>
        </RouterLink>

        <div v-else ref="accountEl" class="account">
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

          <div id="account-panel" class="dropdown-panel account-panel" :class="{ 'is-open': isMenuOpen }">
            <p v-if="authStore.user" class="account-username">{{ authStore.user.username }}</p>

            <div v-if="authStore.isAuthenticated" class="account-section">
              <RouterLink to="/account" class="account-link" @click="closeMenu">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                  <circle cx="12" cy="8.5" r="3.5" />
                  <path d="M4.5 20c1.5-4 5-5.5 7.5-5.5s6 1.5 7.5 5.5" />
                </svg>
                <span>{{ $t('nav.accountSettings') }}</span>
              </RouterLink>
            </div>

            <div v-if="authStore.user?.is_staff" class="account-section">
              <p class="account-section-label">{{ $t('nav.administration') }}</p>
              <RouterLink to="/admin/users" class="account-link" @click="closeMenu">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 3.5l6.5 2.6v5.4c0 4.6-3 7.7-6.5 8.9-3.5-1.2-6.5-4.3-6.5-8.9V6.1L12 3.5Z" />
                </svg>
                <span>{{ $t('nav.admin') }}</span>
              </RouterLink>
              <RouterLink to="/admin/thematic-pages" class="account-link" @click="closeMenu">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="4" y="4" width="7" height="7" rx="1.5" />
                  <rect x="13" y="4" width="7" height="7" rx="1.5" />
                  <rect x="4" y="13" width="7" height="7" rx="1.5" />
                  <rect x="13" y="13" width="7" height="7" rx="1.5" />
                </svg>
                <span>{{ $t('nav.adminThematicPages') }}</span>
              </RouterLink>
              <RouterLink to="/admin/ingredients" class="account-link" @click="closeMenu">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12c0-4 3-7 7-7 0 4-3 7-7 7Z" />
                  <path d="M5 12c4 0 7 3 7 7-4 0-7-3-7-7Z" />
                  <path d="M19 12c0 4-3 7-7 7 0-4 3-7 7-7Z" />
                </svg>
                <span>{{ $t('nav.adminIngredients') }}</span>
              </RouterLink>
            </div>

            <div class="account-section">
              <button class="secondary account-link-button" @click="handleLogout">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3" />
                  <path d="M14 16l4-4-4-4" />
                  <path d="M18 12H8" />
                </svg>
                <span>{{ $t('nav.logout') }}</span>
              </button>
            </div>
          </div>
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
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  text-decoration: none;
  color: var(--color-text);
  font-weight: 600;
}

.top-links a svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.top-links a.router-link-active {
  color: var(--color-primary);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.dice-button {
  background: var(--color-surface-muted);
  color: var(--color-text);
  border-radius: 999px;
  width: 2.75rem;
  height: 2.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dice-button svg {
  width: 20px;
  height: 20px;
}

.dice-button:hover,
.dice-button.router-link-active {
  background: var(--color-primary-soft);
}

.account,
.locale {
  position: relative;
  flex-shrink: 0;
}

.locale-button,
.theme-toggle,
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

.locale-flag {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  box-shadow: 0 0 0 1px var(--color-border);
}

.account-button.router-link-active {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.locale-button:hover,
.theme-toggle:hover,
.account-button:hover {
  background: var(--color-primary-soft);
}

.dropdown-panel {
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

.dropdown-panel.is-open {
  display: flex;
}

.account-username {
  margin: 0;
  font-weight: 700;
}

.account-section {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.account-section + .account-section {
  border-top: 1px solid var(--color-border);
  padding-top: 0.75rem;
}

.account-section-label {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-muted);
}

.account-link,
.account-link-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-primary-dark);
  font-weight: 600;
  text-decoration: none;
  font-size: 0.9rem;
}

.account-link svg,
.account-link-button svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.account-link-button {
  background: none;
  border: none;
  padding: 0;
  min-height: auto;
  cursor: pointer;
}

.locale-panel {
  min-width: 160px;
  padding: 0.4rem;
  gap: 0.15rem;
}

.locale-option {
  justify-content: flex-start;
  background: none;
  color: var(--color-text);
  border-radius: 10px;
  min-height: 2.25rem;
  padding: 0.4rem 0.6rem;
  font-weight: 500;
}

.locale-option:hover {
  background: var(--color-surface-muted);
}

.locale-option[aria-pressed='true'] {
  font-weight: 700;
  color: var(--color-primary-dark);
}

.locale-option-flag {
  width: 22px;
  height: 15px;
  border-radius: 3px;
  box-shadow: 0 0 0 1px var(--color-border);
  flex-shrink: 0;
}

.locale-option-label {
  flex: 1;
  text-align: left;
}

.tabbar {
  display: none;
}

@media (max-width: 600px) {
  .top-links {
    display: none;
  }

  .dice-button {
    display: none;
  }

  .navbar-inner {
    gap: 0.5rem;
  }

  /* Le nom de la marque cède la place aux actions plutôt que de faire déborder la page. */
  .brand {
    min-width: 0;
  }

  .brand-name {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .nav-actions {
    gap: 0.35rem;
    min-width: 0;
  }

  .locale-button,
  .theme-toggle,
  .account-button {
    width: 2.25rem;
    height: 2.25rem;
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
