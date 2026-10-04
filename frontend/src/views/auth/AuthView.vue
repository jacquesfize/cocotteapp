<script setup lang="ts">
import { ArrowRight, Mail, User } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AuthLayout from '../../components/shared/AuthLayout.vue'
import PasswordInput from '../../components/shared/PasswordInput.vue'
import { useAuthStore } from '../../stores/auth'
import { getErrorData } from '../../utils/apiError'
import type { RegisterPayload } from '../../types/api'

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
  health_data_consent: false,
})
const error = ref('')
const passwordErrors = ref<string[]>([])
const emailErrors = ref<string[]>([])
const usernameErrors = ref<string[]>([])
const PASSWORD_MIN_LENGTH = 8
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
  passwordErrors.value = []
  emailErrors.value = []
  usernameErrors.value = []
  if (props.mode === 'register' && registerForm.value.password.length < PASSWORD_MIN_LENGTH) {
    passwordErrors.value = [t('auth.passwordTooShort', { n: PASSWORD_MIN_LENGTH })]
    document.getElementById('password')?.focus()
    return
  }
  isSubmitting.value = true
  try {
    if (props.mode === 'login') {
      await authStore.login(loginForm.value.email, loginForm.value.password)
    } else {
      // Sans consentement, le régime et l'activité ne sont pas envoyés (l'API les refuserait) :
      // ils se renseignent plus tard depuis Mon compte.
      const { diet_type, activity_level, ...account } = registerForm.value
      await authStore.register(
        registerForm.value.health_data_consent ? { ...account, diet_type, activity_level } : account,
      )
    }
    redirectAfterAuth()
  } catch (err) {
    if (props.mode === 'login') {
      error.value = t('auth.invalidCredentials')
    } else {
      const data = getErrorData<{ username?: string[]; email?: string[]; password?: string[] }>(err)
      usernameErrors.value = data?.username ?? []
      emailErrors.value = data?.email ?? []
      passwordErrors.value = data?.password ?? []
      // Le focus va au premier champ en erreur, dans l'ordre d'affichage.
      const firstInvalid = [
        ['username', usernameErrors.value],
        ['email', emailErrors.value],
        ['password', passwordErrors.value],
      ].find(([, msgs]) => msgs.length)
      if (firstInvalid) {
        document.getElementById(firstInvalid[0] as string)?.focus()
      } else {
        error.value = t('auth.registerError')
      }
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
                  :aria-invalid="usernameErrors.length > 0 || undefined"
                  aria-describedby="username-errors"
                />
              </div>
              <ul id="username-errors" class="field-errors" aria-live="polite">
                <li v-for="msg in usernameErrors" :key="msg">{{ msg }}</li>
              </ul>
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
                  :aria-invalid="emailErrors.length > 0 || undefined"
                  aria-describedby="email-errors"
                />
              </div>
              <ul id="email-errors" class="field-errors" aria-live="polite">
                <li v-for="msg in emailErrors" :key="msg">{{ msg }}</li>
              </ul>
            </div>
            <div class="field">
              <label for="password" class="sr-only">{{ $t('auth.password') }}</label>
              <PasswordInput
                id="password"
                v-model="registerForm.password"
                :placeholder="$t('auth.password')"
                autocomplete="new-password"
                :invalid="passwordErrors.length > 0"
                describedby="password-help"
              />
              <div id="password-help" aria-live="polite">
                <ul v-if="passwordErrors.length" class="field-errors">
                  <li v-for="msg in passwordErrors" :key="msg">{{ msg }}</li>
                </ul>
                <p v-else class="muted field-hint">{{ $t('auth.passwordHint', { n: PASSWORD_MIN_LENGTH }) }}</p>
              </div>
            </div>
            <!-- Consentement RGPD (art. 9) : la case dit en une phrase à quoi on consent ; le détail
                 (nature des données, usages, retrait) reste lisible avant de cocher, sous « Pourquoi ? »,
                 hors du <label> pour qu'ouvrir le détail ne coche pas la case. -->
            <div class="consent">
              <label class="consent-choice">
                <input
                  id="health_data_consent"
                  v-model="registerForm.health_data_consent"
                  type="checkbox"
                  aria-describedby="health-consent-hint"
                />
                <span>{{ $t('auth.healthConsent') }}</span>
              </label>
              <p id="health-consent-hint" class="muted consent-hint">{{ $t('auth.healthConsentOptional') }}</p>
              <details class="consent-details">
                <summary>{{ $t('auth.healthConsentWhy') }}</summary>
                <p>{{ $t('auth.healthConsentDetails') }}</p>
              </details>
            </div>
            <div v-if="registerForm.health_data_consent" class="profile-row">
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
            <i18n-t keypath="auth.privacyNotice" tag="p" class="muted privacy-notice" scope="global">
              <template #privacy>
                <RouterLink :to="{ name: 'privacy' }">{{ $t('legal.footerPrivacy') }}</RouterLink>
              </template>
              <template #legal>
                <RouterLink :to="{ name: 'legal' }">{{ $t('legal.footerLegal') }}</RouterLink>
              </template>
            </i18n-t>
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
.field-hint,
.field-errors {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
}

.field-errors {
  padding: 0;
  list-style: none;
  color: var(--color-danger);
  font-weight: 500;
}

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

.consent {
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  line-height: 1.4;
}

.consent-choice {
  display: flex;
  gap: 0.6rem;
  align-items: flex-start;
  cursor: pointer;
  /* Annule le style des libellés de champ (petits, gris) : c'est ici une vraie phrase. */
  font-size: inherit;
  font-weight: 500;
  color: var(--color-text);
}

.consent-choice input {
  width: auto;
  margin-top: 0.2rem;
  flex-shrink: 0;
}

/* Aligné sur le texte de la case, pas sur la case elle-même. */
.consent-hint,
.consent-details {
  margin: 0.2rem 0 0 1.6rem;
  font-size: 0.8rem;
}

.consent-details summary {
  width: fit-content;
  color: var(--color-primary-dark);
  cursor: pointer;
}

.consent-details p {
  margin: 0.35rem 0 0;
  color: var(--color-muted);
}

.privacy-notice {
  font-size: 0.85rem;
  margin: 0.5rem 0 1rem;
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
