<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

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
    error.value = err.response?.data?.username?.[0] || "Impossible de créer le compte."
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="card" style="max-width: 420px; margin: 2rem auto">
    <h1>Inscription</h1>
    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="username">Nom d'utilisateur</label>
        <input id="username" v-model="form.username" required autocomplete="username" />
      </div>
      <div class="field">
        <label for="email">Email</label>
        <input id="email" v-model="form.email" type="email" required autocomplete="email" />
      </div>
      <div class="field">
        <label for="password">Mot de passe</label>
        <input id="password" v-model="form.password" type="password" required autocomplete="new-password" />
      </div>
      <div class="field">
        <label for="diet_type">Régime alimentaire</label>
        <select id="diet_type" v-model="form.diet_type">
          <option value="omnivore">Omnivore</option>
          <option value="vegetarian">Végétarien</option>
          <option value="vegan">Végan</option>
        </select>
      </div>
      <div class="field">
        <label for="activity_level">Niveau d'activité</label>
        <select id="activity_level" v-model="form.activity_level">
          <option value="sedentary">Sédentaire</option>
          <option value="moderate">Modéré</option>
          <option value="athlete">Sportif</option>
        </select>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="isSubmitting">Créer mon compte</button>
    </form>
  </div>
</template>
