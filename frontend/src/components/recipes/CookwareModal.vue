<script setup lang="ts">
import { CookingPot } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import BaseModal from '../shared/BaseModal.vue'
import ImageWithCredit from '../shared/ImageWithCredit.vue'
import type { Cookware } from '../../types/models'

// Fenêtre ouverte au clic sur un matériel (page recette, mode cuisine) : sa photo en grand avec
// son crédit (obligatoire pour une photo CC BY / CC BY-SA), ou à défaut son emoji.
defineProps<{
  cookware: Cookware
  // Lien vers la liste des recettes qui l'utilisent : masqué en mode cuisine, qu'il quitterait.
  showRecipesLink?: boolean
}>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
</script>

<template>
  <BaseModal :title="cookware.name" @close="emit('close')">
    <ImageWithCredit
      v-if="cookware.image"
      class="cookware-modal-photo"
      :image-url="cookware.image"
      :alt="cookware.name"
      :license="cookware.image_license"
      :credit-author="cookware.image_credit_author"
      :credit-source-url="cookware.image_credit_source_url"
      :credit-license-url="cookware.image_credit_license_url"
    />
    <p v-else class="cookware-modal-placeholder" aria-hidden="true">
      <span v-if="cookware.emoji">{{ cookware.emoji }}</span>
      <CookingPot v-else :size="64" />
    </p>
    <RouterLink
      v-if="showRecipesLink"
      :to="{ name: 'recipes', query: { cookware: cookware.slug } }"
      class="cookware-modal-link"
      @click="emit('close')"
    >
      {{ t('cookware.seeRecipes', { name: cookware.name }) }}
    </RouterLink>
  </BaseModal>
</template>

<style scoped>
.cookware-modal-photo :deep(img) {
  width: 100%;
  max-height: 60vh;
  border-radius: 0;
  object-fit: contain;
}

.cookware-modal-placeholder {
  display: flex;
  justify-content: center;
  margin: 1rem 0;
  font-size: 4rem;
  color: var(--color-primary-dark);
}

.cookware-modal-link {
  display: inline-block;
  margin-top: 0.75rem;
  font-weight: 600;
}
</style>
