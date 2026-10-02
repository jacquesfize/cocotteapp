<script setup lang="ts">
import { Clock, Download, EyeOff, Leaf, Lock, Pencil, Trash2, Users } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { formatDuration } from '../utils/format'
import { isImportedRecipe } from '../utils/recipeOrigin'
import AllergenBadges from './AllergenBadges.vue'
import ImageWithCredit from './ImageWithCredit.vue'
import type { Recipe } from '../types/models'

const props = defineProps<{
  recipe: Recipe
  variant?: 'row' | 'tile'
  // Affiche les boutons Modifier/Supprimer (variante ligne, recettes de l'utilisateur uniquement).
  manageable?: boolean
}>()

const emit = defineEmits<{ delete: [recipe: Recipe] }>()

const { t, locale } = useI18n()
const authStore = useAuthStore()

const MAX_TAGS = 3

const isRow = computed(() => props.variant !== 'tile')
const isOwner = computed(() => Boolean(authStore.user) && props.recipe.author_id === authStore.user?.id)
const isImported = computed(() => isImportedRecipe(props.recipe))
// "importé par X" toujours affiché (même pour ses propres recettes) ; "par X" seulement pour
// les recettes des autres.
const authorLine = computed(() => {
  if (!props.recipe.author) return null
  if (isImported.value) return t('recipes.importedBy', { author: props.recipe.author })
  return isOwner.value ? null : t('recipes.byAuthor', { author: props.recipe.author })
})
const showActions = computed(() => isRow.value && props.manageable && isOwner.value)

const timeDetail = computed(() => {
  const { prep_time_minutes: prep, cook_time_minutes: cook } = props.recipe
  if (!prep || !cook) return undefined
  return `${formatDuration(prep)} ${t('recipes.prep')} · ${formatDuration(cook)} ${t('recipes.cook')}`
})

// Mêmes seuils que le filtre "Impact carbone par portion" (RecipeFilters.vue).
const carbon = computed(() => {
  const kg = props.recipe.carbon_footprint_kg_co2e
  if (kg === undefined || kg === null) return null
  const level = kg <= 0.5 ? 'low' : kg <= 1.5 ? 'medium' : 'high'
  const formatted = new Intl.NumberFormat(locale.value, { maximumFractionDigits: 1 }).format(kg)
  return { level, label: t('recipes.carbonPerServing', { kg: formatted }) }
})

const visibleTags = computed(() => (props.recipe.tags ?? []).slice(0, MAX_TAGS))
const hiddenTagCount = computed(() => Math.max(0, (props.recipe.tags?.length ?? 0) - MAX_TAGS))
</script>

<template>
  <article class="recipe-card" :class="{ tile: !isRow }">
    <ImageWithCredit
      v-if="recipe.image || recipe.image_url"
      class="thumb-wrapper"
      :image-url="recipe.image || recipe.image_url"
      :source-url="recipe.image ? null : recipe.source_url"
      :license="recipe.image_license"
      :credit-author="recipe.image_credit_author"
      :credit-source-url="recipe.image_credit_source_url"
      :credit-license-url="recipe.image_credit_license_url"
      :credit-note="recipe.image_credit_note"
      :compact="isRow"
      :overlay="!isRow"
      overlay-align="right"
    />
    <div v-else-if="!isRow" class="thumb thumb-placeholder" aria-hidden="true">🍲</div>
    <div v-if="!isRow" class="scrim" />
    <div class="recipe-card-body">
      <h3>
        <!-- Lien "étiré" (::after) sur toute la carte : la carte reste cliquable partout sans
             imbriquer les boutons d'action dans un <a>, ce qui serait du HTML invalide. -->
        <RouterLink :to="{ name: 'recipe-detail', params: { id: recipe.id } }" class="card-link">
          {{ recipe.title }}
        </RouterLink>
        <Lock v-if="recipe.content_restricted" :size="14" class="restricted-icon" :aria-label="$t('recipes.restrictedNotice')" />
      </h3>

      <p v-if="!isRow" class="muted">
        {{ $t(`diet.${recipe.diet_type}`) }} · {{ formatDuration(recipe.total_time_minutes) }}
      </p>
      <ul v-else class="meta">
        <li class="diet-badge" :class="`diet-${recipe.diet_type}`">{{ $t(`diet.${recipe.diet_type}`) }}</li>
        <li
          v-if="recipe.average_rating != null"
          class="rating-badge"
          :title="$t('ratings.average', { value: recipe.average_rating.toFixed(1), count: recipe.ratings_count })"
        >
          ★ {{ recipe.average_rating.toFixed(1) }}
        </li>
        <li :title="timeDetail"><Clock :size="14" />{{ formatDuration(recipe.total_time_minutes) }}</li>
        <li v-if="recipe.servings"><Users :size="14" />{{ recipe.servings }} {{ $t('recipes.servings') }}</li>
        <li v-if="carbon" class="carbon" :class="`carbon-${carbon.level}`" :title="$t('recipes.carbonFootprint')">
          <Leaf :size="14" />{{ carbon.label }}
        </li>
        <li v-if="recipe.is_public === false" class="private-badge"><EyeOff :size="14" />{{ $t('recipes.privateBadge') }}</li>
        <li v-if="authorLine" class="author"><Download v-if="isImported" :size="14" />{{ authorLine }}</li>
      </ul>

      <ul v-if="isRow && (visibleTags.length || recipe.version_label)" class="tags">
        <li v-if="recipe.version_label" class="tag version-tag">{{ recipe.version_label }}</li>
        <li v-for="tag in visibleTags" :key="tag.id" class="tag">{{ tag.name }}</li>
        <li v-if="hiddenTagCount" class="tag more-tag">+{{ hiddenTagCount }}</li>
      </ul>

      <AllergenBadges :allergens="recipe.allergens ?? []" only-mine class="card-allergens" />
      <p v-if="recipe.description" class="description">{{ recipe.description }}</p>
    </div>

    <div v-if="showActions" class="card-actions">
      <RouterLink
        :to="{ name: 'recipe-edit', params: { id: recipe.id } }"
        class="action-btn"
        :title="$t('common.edit')"
        :aria-label="`${$t('common.edit')} — ${recipe.title}`"
      >
        <Pencil :size="16" />
      </RouterLink>
      <button
        type="button"
        class="action-btn danger-btn"
        :title="$t('common.delete')"
        :aria-label="`${$t('common.delete')} — ${recipe.title}`"
        @click="emit('delete', recipe)"
      >
        <Trash2 :size="16" />
      </button>
    </div>
  </article>
</template>

<style scoped>
.recipe-card {
  position: relative;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  color: inherit;
  padding: 1rem 1.25rem;
  transition: background-color 0.15s ease;
}

.recipe-card:not(:last-child) {
  border-bottom: 1px solid var(--color-border);
}

.recipe-card:hover {
  background: var(--color-surface-hover, rgba(127, 127, 127, 0.08));
}

.card-link {
  color: inherit;
  text-decoration: none;
}

.card-link::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
}

.card-link:focus-visible {
  outline: none;
}

.card-link:focus-visible::after {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.thumb-wrapper {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
}

.thumb-wrapper :deep(img) {
  width: 88px;
  height: 88px;
  object-fit: cover;
  border-radius: 12px;
  flex-shrink: 0;
}

.thumb-wrapper :deep(.image-credit-line) {
  max-width: 88px;
  font-size: 0.6rem;
}

/* Utilisé uniquement par le placeholder (pas de photo) : la vraie photo est stylée via
   `.thumb-wrapper :deep(img)` ci-dessus, car l'<img> vit dans ImageWithCredit. */
.thumb {
  width: 88px;
  height: 88px;
  border-radius: 12px;
  flex-shrink: 0;
}

.recipe-card-body {
  flex: 1;
  min-width: 0;
}

.recipe-card h3 {
  margin: 0 0 0.4rem;
  line-height: 1.3;
}

.restricted-icon {
  vertical-align: middle;
  margin-left: 0.3rem;
  color: var(--color-muted);
}

.meta,
.tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.9rem;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 0.85rem;
  color: var(--color-muted);
}

.meta li {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.diet-badge {
  padding: 0.1rem 0.55rem;
  border-radius: var(--radius-pill);
  font-weight: 600;
  font-size: 0.78rem;
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.diet-vegetarian {
  background: color-mix(in srgb, var(--color-vegetarian) 15%, var(--color-surface));
  color: color-mix(in srgb, var(--color-vegetarian) 75%, var(--color-text));
}

.diet-vegan {
  background: color-mix(in srgb, var(--color-vegan) 20%, var(--color-surface));
  color: color-mix(in srgb, var(--color-vegan) 80%, var(--color-text));
}

.rating-badge {
  color: var(--color-primary-dark);
  font-weight: 600;
}

.carbon-low {
  color: color-mix(in srgb, var(--color-vegetarian) 80%, var(--color-text));
}

.carbon-medium {
  color: color-mix(in srgb, var(--color-carbon-medium) 85%, var(--color-text));
}

.carbon-high {
  color: var(--color-danger);
}

.private-badge {
  font-style: italic;
}

.tags {
  gap: 0.3rem;
  margin-top: 0.5rem;
}

.tag {
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  font-size: 0.75rem;
}

.version-tag {
  border-color: transparent;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  font-weight: 600;
}

.card-allergens {
  margin-top: 0.5rem;
}

.description {
  margin: 0.5rem 0 0;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* Au-dessus du lien étiré pour rester cliquables. */
.card-actions {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 0.35rem;
  flex-shrink: 0;
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.recipe-card:hover .card-actions,
.card-actions:focus-within {
  opacity: 1;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  min-height: 2.25rem;
  padding: 0;
  border-radius: 999px;
  background: var(--color-surface-muted);
  color: var(--color-text);
  text-decoration: none;
}

.action-btn:hover {
  background: var(--color-primary-soft-hover);
  color: var(--color-primary-dark);
}

.action-btn.danger-btn:hover {
  background: var(--color-danger-soft-hover);
  color: var(--color-danger);
}

@media (max-width: 600px) {
  .recipe-card {
    padding: 0.85rem 1rem;
    gap: 0.75rem;
  }

  .thumb-wrapper :deep(img) {
    width: 64px;
    height: 64px;
  }

  .thumb-wrapper :deep(.image-credit-line) {
    max-width: 64px;
  }

  .thumb {
    width: 64px;
    height: 64px;
  }

  /* Pas de survol sur mobile : actions toujours visibles. */
  .card-actions {
    flex-direction: column;
    opacity: 1;
  }
}

/* Variante tuile (accueil) : le corps reste un élément flex non positionné pour que le
   ::after du lien s'étende sur toute la tuile ; z-index sur un élément flex suffit à le
   peindre au-dessus de l'image positionnée. */
.recipe-card.tile {
  display: flex;
  align-items: flex-end;
  aspect-ratio: 1;
  padding: 0;
  overflow: hidden;
  border-radius: 16px;
  border-bottom: 0;
  color: var(--color-on-primary);
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
}

.tile .thumb-wrapper {
  position: absolute;
  inset: 0;
}

.tile .thumb-wrapper :deep(.image-with-credit-frame) {
  height: 100%;
}

.tile .thumb-wrapper :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 0;
}

.tile .thumb {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: 0;
}

.thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  background: var(--color-primary-soft);
}

.scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0) 60%);
}

.tile .recipe-card-body {
  z-index: 1;
  padding: 0 0.85rem 0.75rem;
}

.tile h3 {
  margin: 0 0 0.15rem;
  font-size: 1rem;
  line-height: 1.25;
  color: inherit;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tile .muted {
  margin: 0;
  font-size: 0.8rem;
  color: inherit;
  opacity: 0.9;
}
</style>
