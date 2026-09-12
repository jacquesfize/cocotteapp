<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()

const form = ref({
  username: '',
  email: '',
  password: '',
  diet_type: 'omnivore',
  activity_level: 'moderate',
})
const error = ref('')
const isSubmitting = ref(false)

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true
  try {
    await authStore.register(form.value)
    router.push({ name: 'recipes' })
  } catch (err) {
    error.value = err.response?.data?.username?.[0] || t('auth.registerError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="card auth-card">
    <h1>{{ $t('auth.registerTitle') }}</h1>
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="username">{{ $t('auth.username') }}</label>
        <input id="username" v-model="form.username" required autocomplete="username" />
      </div>
      <div class="field">
        <label for="email">{{ $t('auth.email') }}</label>
        <input id="email" v-model="form.email" type="email" required autocomplete="email" />
      </div>
      <div class="field">
        <label for="password">{{ $t('auth.password') }}</label>
        <input id="password" v-model="form.password" type="password" required autocomplete="new-password" />
      </div>
      <div class="field">
        <label for="diet_type">{{ $t('auth.dietType') }}</label>
        <select id="diet_type" v-model="form.diet_type">
          <option value="omnivore">{{ $t('diet.omnivore') }}</option>
          <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
          <option value="vegan">{{ $t('diet.vegan') }}</option>
        </select>
      </div>
      <div class="field">
        <label for="activity_level">{{ $t('auth.activityLevel') }}</label>
        <select id="activity_level" v-model="form.activity_level">
          <option value="sedentary">{{ $t('activityLevel.sedentary') }}</option>
          <option value="moderate">{{ $t('activityLevel.moderate') }}</option>
          <option value="athlete">{{ $t('activityLevel.athlete') }}</option>
        </select>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="isSubmitting">{{ $t('auth.registerButton') }}</button>
    </form>
  </div>
</template>

<style scoped>
.auth-card {
  max-width: 420px;
  margin: 2rem auto;
}
</style>
