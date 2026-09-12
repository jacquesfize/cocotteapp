<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const error = ref('')
const isSubmitting = ref(false)

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true
  try {
    await authStore.login(username.value, password.value)
    router.push(route.query.redirect || { name: 'recipes' })
  } catch {
    error.value = 'Identifiants invalides.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="card" style="max-width: 360px; margin: 2rem auto">
    <h1>Connexion</h1>
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="username">Nom d'utilisateur</label>
        <input id="username" v-model="username" required autocomplete="username" />
      </div>
      <div class="field">
        <label for="password">Mot de passe</label>
        <input id="password" v-model="password" type="password" required autocomplete="current-password" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="isSubmitting">Se connecter</button>
    </form>
    <p class="muted">
      Pas encore de compte ? <RouterLink to="/register">S'inscrire</RouterLink>
    </p>
  </div>
</template>
