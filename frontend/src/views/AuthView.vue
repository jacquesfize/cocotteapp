<script setup lang="ts">
import { ArrowRight, Mail, User } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AuthLayout from '../components/AuthLayout.vue'
import PasswordInput from '../components/PasswordInput.vue'
import { useAuthStore } from '../stores/auth'
import type { RegisterPayload } from '../types/api'

// Connexion et inscription partagent la même page : /login et /register ne diffèrent que par l'onglet actif.
const props = defineProps<{ mode: 'login' | 'register' }>()

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const loginForm = ref({ email: '', password: '' })
const registerForm = ref<RegisterPayload>({
  username: '',
  email: '',
  password: '',
  diet_type: 'omnivore',
  activity_level: 'moderate',
})
const error = ref('')
const isSubmitting = ref(false)

// Les deux formulaires n'ont pas la même hauteur : on suit celle du contenu pour l'animer en CSS
// plutôt que de laisser la carte sauter d'un coup au changement d'onglet.
const formsInner = ref<HTMLElement | null>(null)
const formsHeight = ref<string>()
let resizeObserver: ResizeObserver | undefined

onMounted(() => {
  if (typeof ResizeObserver === 'undefined' || !formsInner.value) return
  resizeObserver = new ResizeObserver(([entry]) => {
    formsHeight.value = `${entry.contentRect.height}px`
  })
  resizeObserver.observe(formsInner.value)
})

onBeforeUnmount(() => resizeObserver?.disconnect())

function redirectAfterAuth() {
  router.push((route.query.redirect as string) || { name: 'recipes' })
}

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true
  try {
    if (props.mode === 'login') {
      await authStore.login(loginForm.value.email, loginForm.value.password)
    } else {
      await authStore.register(registerForm.value)
    }
    redirectAfterAuth()
  } catch (err) {
    if (props.mode === 'login') {
      error.value = t('auth.invalidCredentials')
    } else {
      const data = (err as { response?: { data?: { username?: string[] } } }).response?.data
      error.value = data?.username?.[0] || t('auth.registerError')
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AuthLayout :title="mode === 'login' ? $t('auth.loginTitle') : $t('auth.registerTitle')">
    <nav class="auth-tabs" :aria-label="$t('auth.tabsLabel')">
      <RouterLink
        :to="{ name: 'login', query: route.query }"
        :aria-current="mode === 'login' ? 'page' : undefined"
        :class="{ active: mode === 'login' }"
        @click="error = ''"
      >
        {{ $t('auth.loginTab') }}
      </RouterLink>
      <RouterLink
        :to="{ name: 'register', query: route.query }"
        :aria-current="mode === 'register' ? 'page' : undefined"
        :class="{ active: mode === 'register' }"
        @click="error = ''"
      >
        {{ $t('auth.registerTab') }}
      </RouterLink>
    </nav>

    <div class="auth-forms" :style="{ height: formsHeight }">
      <div ref="formsInner">
        <Transition name="form-fade" mode="out-in">
          <form v-if="mode === 'login'" key="login" class="auth-form" @submit.prevent="handleSubmit">
            <p v-if="route.query.resetDone === 'true'" class="muted">{{ $t('auth.resetPasswordSuccess') }}</p>
            <div class="field">
              <label for="email" class="sr-only">{{ $t('auth.email') }}</label>
              <div class="input-icon">
                <Mail :size="18" />
                <input
                  id="email"
                  v-model="loginForm.email"
                  type="email"
                  :placeholder="$t('auth.email')"
                  required
                  autocomplete="email"
                />
              </div>
            </div>
            <div class="field">
              <label for="password" class="sr-only">{{ $t('auth.password') }}</label>
              <PasswordInput
                id="password"
                v-model="loginForm.password"
                :placeholder="$t('auth.password')"
                autocomplete="current-password"
              />
            </div>
            <div class="auth-links">
              <RouterLink to="/forgot-password">{{ $t('auth.forgotPassword') }}</RouterLink>
            </div>
            <p v-if="error" class="error">{{ error }}</p>
            <button type="submit" :disabled="isSubmitting">
              {{ $t('auth.loginButton') }}
              <ArrowRight :size="18" />
            </button>
          </form>

          <form v-else key="register" class="auth-form" @submit.prevent="handleSubmit">
            <div class="field">
              <label for="username" class="sr-only">{{ $t('auth.username') }}</label>
              <div class="input-icon">
                <User :size="18" />
                <input
                  id="username"
                  v-model="registerForm.username"
                  :placeholder="$t('auth.username')"
                  required
                  autocomplete="username"
                />
              </div>
            </div>
            <div class="field">
              <label for="email" class="sr-only">{{ $t('auth.email') }}</label>
              <div class="input-icon">
                <Mail :size="18" />
                <input
                  id="email"
                  v-model="registerForm.email"
                  type="email"
                  :placeholder="$t('auth.email')"
                  required
                  autocomplete="email"
                />
              </div>
            </div>
            <div class="field">
              <label for="password" class="sr-only">{{ $t('auth.password') }}</label>
              <PasswordInput
                id="password"
                v-model="registerForm.password"
                :placeholder="$t('auth.password')"
                autocomplete="new-password"
              />
            </div>
            <div class="profile-row">
              <div class="field">
                <label for="diet_type">{{ $t('auth.dietType') }}</label>
                <select id="diet_type" v-model="registerForm.diet_type">
                  <option value="omnivore">{{ $t('diet.omnivore') }}</option>
                  <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
                  <option value="vegan">{{ $t('diet.vegan') }}</option>
                </select>
              </div>
              <div class="field">
                <label for="activity_level">{{ $t('auth.activityLevel') }}</label>
                <select id="activity_level" v-model="registerForm.activity_level">
                  <option value="sedentary">{{ $t('activityLevel.sedentary') }}</option>
                  <option value="moderate">{{ $t('activityLevel.moderate') }}</option>
                  <option value="athlete">{{ $t('activityLevel.athlete') }}</option>
                </select>
              </div>
            </div>
            <p v-if="error" class="error">{{ error }}</p>
            <button type="submit" :disabled="isSubmitting">
              {{ $t('auth.registerButton') }}
              <ArrowRight :size="18" />
            </button>
          </form>
        </Transition>
      </div>
    </div>
  </AuthLayout>
</template>

<style scoped>
.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.25rem;
  padding: 0.25rem;
  margin-bottom: 1.5rem;
  background: var(--color-surface-muted);
  border-radius: 999px;
}

.auth-tabs a {
  text-align: center;
  padding: 0.55rem 0.75rem;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 600;
  color: var(--color-muted);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.auth-tabs a:hover {
  color: var(--color-text);
}

.auth-tabs a.active {
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: var(--shadow-card);
}

.auth-forms {
  overflow: hidden;
  transition: height 0.3s ease;
}

.form-fade-enter-active,
.form-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.form-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.form-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (prefers-reduced-motion: reduce) {
  .auth-forms,
  .form-fade-enter-active,
  .form-fade-leave-active {
    transition: none;
  }
}

.profile-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

@media (max-width: 400px) {
  .profile-row {
    grid-template-columns: 1fr;
  }
}
</style>
