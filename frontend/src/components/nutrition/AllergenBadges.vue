<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { allergenEmoji } from '../../utils/allergens'

const props = defineProps<{
  allergens: string[]
  unverified?: boolean
  // Mode compact (cartes de liste) : seuls les allergènes du profil de l'utilisateur.
  onlyMine?: boolean
}>()

const authStore = useAuthStore()

const allergies = computed(() => authStore.user?.allergies ?? [])
const intolerances = computed(() => authStore.user?.intolerances ?? [])

function severity(slug: string): 'allergy' | 'intolerance' | 'neutral' {
  if (allergies.value.includes(slug)) return 'allergy'
  if (intolerances.value.includes(slug)) return 'intolerance'
  return 'neutral'
}

const badges = computed(() =>
  props.allergens
    .map((slug) => ({ slug, severity: severity(slug) }))
    .filter((b) => !props.onlyMine || b.severity !== 'neutral')
    // Allergies d'abord, puis intolérances, puis le reste.
    .sort((a, b) => ['allergy', 'intolerance', 'neutral'].indexOf(a.severity) - ['allergy', 'intolerance', 'neutral'].indexOf(b.severity)),
)
</script>

<template>
  <div v-if="badges.length || (unverified && !onlyMine)" class="allergen-badges">
    <span
      v-for="badge in badges"
      :key="badge.slug"
      class="allergen-badge"
      :class="badge.severity"
      :data-testid="`allergen-${badge.slug}`"
    >
      <span aria-hidden="true">{{ allergenEmoji(badge.slug) }}</span>{{ $t(`allergen.${badge.slug}`) }}
    </span>
    <span v-if="unverified && !onlyMine" class="allergen-unverified muted">{{ $t('allergens.unverified') }}</span>
  </div>
</template>

<style scoped>
.allergen-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}

.allergen-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.6rem;
  border-radius: 0;
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.allergen-badge.allergy {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.allergen-badge.intolerance {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.allergen-unverified {
  font-size: 0.75rem;
}
</style>
