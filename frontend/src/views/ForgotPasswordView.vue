<script setup lang="ts">
import { KeyRound } from '@lucide/vue'
import { ref } from 'vue'
import PageHeader from '../components/shared/PageHeader.vue'
import { requestPasswordReset } from '../api/auth'

const email = ref('')
const isSubmitting = ref(false)
const isDone = ref(false)

async function handleSubmit() {
  isSubmitting.value = true
  try {
    await requestPasswordReset(email.value)
  } finally {
    isSubmitting.value = false
    // Toujours le même message, que l'email corresponde à un compte ou non.
    isDone.value = true
  }
}
</script>

<template>
  <div class="card auth-card">
    <PageHeader :icon="KeyRound" :title="$t('auth.forgotPasswordTitle')" />

    <p v-if="isDone" class="muted">{{ $t('auth.forgotPasswordSent') }}</p>

    <form v-else @submit.prevent="handleSubmit">
      <p class="muted">{{ $t('auth.forgotPasswordDescription') }}</p>
      <div class="field">
        <label for="email">{{ $t('auth.email') }}</label>
        <input id="email" v-model="email" type="email" required autocomplete="email" />
      </div>
      <button type="submit" :disabled="isSubmitting">{{ $t('auth.forgotPasswordButton') }}</button>
    </form>

    <p class="muted">
      <RouterLink to="/login">{{ $t('auth.backToLogin') }}</RouterLink>
    </p>
  </div>
</template>

<style scoped>
.auth-card {
  max-width: 360px;
  margin: 2rem auto;
}
</style>
