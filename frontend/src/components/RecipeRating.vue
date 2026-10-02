<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { rateRecipe, type RecipeRatingResult } from '../api/recipes'
import { getErrorStatus } from '../utils/apiError'

const props = defineProps<{
  recipeId: number | string
  averageRating: number | null
  ratingsCount: number
  myRating: number | null
}>()

const emit = defineEmits<{
  rated: [result: RecipeRatingResult]
}>()

const { t } = useI18n()

const hoverValue = ref(0)
const isSubmitting = ref(false)
const submitError = ref('')

async function rate(value: number) {
  if (isSubmitting.value) return
  submitError.value = ''
  isSubmitting.value = true
  try {
    const result = await rateRecipe(props.recipeId, value)
    emit('rated', result)
  } catch (err) {
    const status = getErrorStatus(err)
    submitError.value = status === 429 ? t('ratings.throttled') : t('ratings.submitError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="rating">
    <span v-if="averageRating != null" class="rating-average">
      {{ $t('ratings.average', { value: averageRating.toFixed(1), count: ratingsCount }) }}
    </span>
    <span v-else class="muted rating-average">{{ $t('ratings.none') }}</span>

    <div
      class="rating-stars"
      role="group"
      :aria-label="$t('ratings.rateAction')"
      @mouseleave="hoverValue = 0"
    >
      <button
        v-for="star in 5"
        :key="star"
        type="button"
        class="rating-star"
        :class="{ filled: star <= (hoverValue || myRating || 0) }"
        :disabled="isSubmitting"
        :aria-label="$t('ratings.starLabel', { count: star })"
        :aria-pressed="myRating === star"
        @mouseenter="hoverValue = star"
        @click="rate(star)"
      >
        ★
      </button>
    </div>

    <p v-if="myRating" class="muted rating-mine">{{ $t('ratings.yours', { value: myRating }) }}</p>
    <p v-if="submitError" class="error">{{ submitError }}</p>
  </div>
</template>

<style scoped>
.rating {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.25rem 0 0.75rem;
}

.rating-average {
  font-size: 0.9rem;
}

.rating-stars {
  display: inline-flex;
  gap: 0.15rem;
}

.rating-star {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 1.3rem;
  line-height: 1;
  color: var(--color-border, #d0d0d0);
}

.rating-star:disabled {
  cursor: default;
}

.rating-star.filled {
  color: var(--color-primary);
}

.rating-mine {
  margin: 0;
  font-size: 0.85rem;
}
</style>
