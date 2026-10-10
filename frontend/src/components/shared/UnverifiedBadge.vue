<script setup lang="ts">
import { ShieldQuestion } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

// Pastille « Non vérifié » d'un ingrédient ou d'un matériel créé par un utilisateur : l'infobulle
// (attribut `title`, doublée d'un texte lu par les lecteurs d'écran) explique qu'un administrateur
// va le vérifier et que son auteur peut le modifier d'ici là. `createdBy` ajoute « ajouté par … »
// (file de revue des administrateurs).
const props = defineProps<{
  createdBy?: string | null
}>()

const { t } = useI18n()
const tooltip = computed(() => t('libraryReview.unverifiedTooltip'))
</script>

<template>
  <span class="unverified-badge" :title="tooltip" data-testid="unverified-badge">
    <ShieldQuestion :size="12" aria-hidden="true" />
    {{ t('libraryReview.unverified') }}<template v-if="props.createdBy"> · {{ t('libraryReview.addedBy', { username: props.createdBy }) }}</template>
    <span class="unverified-badge-sr">{{ tooltip }}</span>
  </span>
</template>

<style scoped>
.unverified-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.05rem 0.5rem;
  border: 1px solid color-mix(in srgb, var(--color-carbon-medium) 45%, var(--color-surface));
  border-radius: var(--radius-pill);
  background: color-mix(in srgb, var(--color-carbon-medium) 14%, var(--color-surface));
  color: color-mix(in srgb, var(--color-carbon-medium) 55%, var(--color-text));
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.5;
  white-space: nowrap;
  vertical-align: middle;
  cursor: help;
}

.unverified-badge-sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
</style>
