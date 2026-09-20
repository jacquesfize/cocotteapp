<script setup lang="ts">
import { TriangleAlert } from '@lucide/vue'
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { allergenEmoji, matchUserAllergens } from '../utils/allergens'

// Avertissement (non bloquant) quand une recette contient un allergène du profil.
const props = defineProps<{ allergens?: string[] }>()

const authStore = useAuthStore()
const matches = computed(() => matchUserAllergens(props.allergens, authStore.user))
</script>

<template>
  <div v-if="matches.allergies.length || matches.intolerances.length" class="allergen-warning" role="alert">
    <p v-if="matches.allergies.length" class="allergy" data-testid="warning-allergy">
      <TriangleAlert :size="14" />{{ $t('allergens.allergyWarning') }}
      <span v-for="slug in matches.allergies" :key="slug" class="item">
        <span aria-hidden="true">{{ allergenEmoji(slug) }}</span>{{ $t(`allergen.${slug}`) }}
      </span>
    </p>
    <p v-if="matches.intolerances.length" class="intolerance" data-testid="warning-intolerance">
      <TriangleAlert :size="14" />{{ $t('allergens.intoleranceWarning') }}
      <span v-for="slug in matches.intolerances" :key="slug" class="item">
        <span aria-hidden="true">{{ allergenEmoji(slug) }}</span>{{ $t(`allergen.${slug}`) }}
      </span>
    </p>
  </div>
</template>

<style scoped>
.allergen-warning p {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3rem;
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  font-weight: 600;
}

.allergy {
  color: var(--color-danger);
}

.intolerance {
  color: var(--color-primary-dark);
}

.item {
  display: inline-flex;
  gap: 0.2rem;
}
</style>
