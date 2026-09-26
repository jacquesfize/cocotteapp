<script setup lang="ts">
import { Eye, EyeOff, Lock } from '@lucide/vue'
import { ref } from 'vue'

defineProps<{ id: string; placeholder: string; autocomplete: string }>()
const model = defineModel<string>({ required: true })

const isVisible = ref(false)
</script>

<template>
  <div class="input-icon">
    <Lock :size="18" />
    <input
      :id="id"
      v-model="model"
      :type="isVisible ? 'text' : 'password'"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      class="has-toggle"
      required
    />
    <!-- Libellé volontairement sans "mot de passe" : getByLabel('Mot de passe') doit rester univoque. -->
    <button
      type="button"
      class="password-toggle"
      :aria-label="isVisible ? $t('auth.hideInput') : $t('auth.showInput')"
      :aria-pressed="isVisible"
      @click="isVisible = !isVisible"
    >
      <EyeOff v-if="isVisible" :size="20" />
      <Eye v-else :size="20" />
    </button>
  </div>
</template>

<style scoped>
.password-toggle {
  position: absolute;
  right: 0.35rem;
  width: 2.25rem;
  min-height: 2.25rem;
  padding: 0;
  background: transparent;
  color: var(--color-muted);
}

.password-toggle:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}
</style>
