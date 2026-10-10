<script setup lang="ts">
import PersonalTagChip from './PersonalTagChip.vue'
import type { PersonalTag } from '../../types/models'

// Avant de créer une étiquette, montre celles qui lui ressemblent déjà (accent, pluriel, faute
// de frappe — voir apps/recipes/personal_tags.py) : un clic en réutilise une plutôt que de créer
// un doublon. Le slot accueille les actions propres à l'écran (« Créer quand même »...).
defineProps<{
  tags: PersonalTag[]
}>()

const emit = defineEmits<{ pick: [tag: PersonalTag] }>()
</script>

<template>
  <div class="similar-tags" role="status">
    <p>{{ $t('personalTags.similarIntro') }}</p>
    <ul>
      <li v-for="tag in tags" :key="tag.id">
        <button
          type="button"
          class="similar-tag-button"
          :title="$t('personalTags.useExisting', { name: tag.name })"
          @click="emit('pick', tag)"
        >
          <PersonalTagChip :tag="tag" />
        </button>
      </li>
    </ul>
    <slot />
  </div>
</template>

<style scoped>
.similar-tags {
  margin-top: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-radius: 0;
  background: var(--color-surface-muted);
  font-size: 0.9rem;
}

.similar-tags p {
  margin: 0 0 0.4rem;
}

.similar-tags ul {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0 0 0.5rem;
  padding: 0;
  list-style: none;
}

.similar-tag-button {
  min-height: auto;
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
}

.similar-tag-button:hover .personal-tag,
.similar-tag-button:focus-visible .personal-tag {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}
</style>
