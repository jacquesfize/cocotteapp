<script setup lang="ts">
import { Search } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import BaseModal from '../shared/BaseModal.vue'
import { suggestFreeImages } from '../../api/importer'
import { imageLicenseLabelKey } from '../../utils/imageCredit'
import type { FreeImageSuggestion } from '../../types/models'

// Recherche d'images libres de droits (Openverse, via le backend) pour illustrer une recette : une
// recette importée ne reprend jamais la photo de son site source (droit d'auteur du photographe).
// Choisir une image la renvoie au parent avec ses champs de crédit déjà remplis.
const props = defineProps<{
  initialQuery: string
}>()

const emit = defineEmits<{
  select: [suggestion: FreeImageSuggestion]
  close: []
}>()

const query = ref(props.initialQuery)
const suggestions = ref<FreeImageSuggestion[]>([])
const isLoading = ref(false)
const hasSearched = ref(false)
const hasError = ref(false)

async function search() {
  const value = query.value.trim()
  if (!value) return
  isLoading.value = true
  hasError.value = false
  try {
    suggestions.value = await suggestFreeImages(value)
  } catch {
    suggestions.value = []
    hasError.value = true
  } finally {
    isLoading.value = false
    hasSearched.value = true
  }
}

// La miniature est servie par le proxy d'Openverse, qui échoue parfois (424) : on se rabat alors
// sur l'image d'origine plutôt que d'afficher une vignette vide.
function useOriginalOnError(event: Event, suggestion: FreeImageSuggestion) {
  const img = event.target as HTMLImageElement
  if (img.src !== suggestion.url) img.src = suggestion.url
}

onMounted(search)
</script>

<template>
  <BaseModal :title="$t('freeImages.title')" @close="emit('close')">
    <p class="muted free-images-hint">{{ $t('freeImages.hint') }}</p>
    <form class="row free-images-search" @submit.prevent="search">
      <input v-model="query" type="search" :aria-label="$t('freeImages.searchLabel')" />
      <button type="submit" :disabled="isLoading || !query.trim()">
        <Search :size="16" />{{ $t('freeImages.search') }}
      </button>
    </form>

    <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
    <p v-else-if="hasError" class="error">{{ $t('freeImages.error') }}</p>
    <p v-else-if="hasSearched && !suggestions.length" class="muted">{{ $t('freeImages.empty') }}</p>
    <ul v-else class="free-images-grid">
      <li v-for="suggestion in suggestions" :key="suggestion.url">
        <button
          type="button"
          class="free-image"
          :aria-label="$t('freeImages.pick', { title: suggestion.title || suggestion.url })"
          @click="emit('select', suggestion)"
        >
          <img
            :src="suggestion.thumbnail"
            alt=""
            loading="lazy"
            @error="useOriginalOnError($event, suggestion)"
          />
          <span class="free-image-credit">
            {{ suggestion.image_credit_author || $t('imageCredit.notSpecified') }} ·
            {{ $t(imageLicenseLabelKey(suggestion.image_license)) }}
          </span>
        </button>
      </li>
    </ul>
    <p class="muted free-images-provider">{{ $t('freeImages.provider') }}</p>
  </BaseModal>
</template>

<style scoped>
.free-images-hint {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
}

.free-images-search {
  flex-wrap: nowrap;
  margin-bottom: 1rem;
}

.free-images-search input {
  flex: 1;
  min-width: 0;
}

.free-images-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
}

.free-image {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  gap: 0.35rem;
  width: 100%;
  padding: 0;
  border: 1.5px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-surface);
  color: inherit;
  text-align: left;
}

.free-image:hover,
.free-image:focus-visible {
  border-color: var(--color-primary);
}

.free-image img {
  display: block;
  width: 100%;
  height: 100px;
  object-fit: cover;
}

.free-image-credit {
  display: block;
  min-width: 0;
  padding: 0 0.5rem 0.45rem;
  font-size: 0.72rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.free-images-provider {
  margin: 1rem 0 0;
  font-size: 0.75rem;
}
</style>
