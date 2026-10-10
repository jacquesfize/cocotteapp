<script setup lang="ts">
import { Check } from '@lucide/vue'
import { TAG_COLOR_NAMES, tagHueStyle } from '../../utils/personalTags'
import type { TagColor } from '../../types/models'

// Choix de la couleur d'une étiquette personnelle parmi la palette fermée (utils/personalTags.ts).
const color = defineModel<TagColor>({ required: true })

defineProps<{
  name: string
}>()
</script>

<template>
  <div class="color-picker" role="radiogroup" :aria-label="$t('personalTags.color')">
    <label
      v-for="option in TAG_COLOR_NAMES"
      :key="option"
      class="swatch"
      :class="{ 'is-selected': color === option }"
      :style="tagHueStyle(option)"
      :title="$t(`personalTags.colors.${option}`)"
    >
      <input v-model="color" type="radio" :name="name" :value="option" class="visually-hidden" />
      <span class="visually-hidden">{{ $t(`personalTags.colors.${option}`) }}</span>
      <Check v-if="color === option" :size="14" aria-hidden="true" />
    </label>
  </div>
</template>

<style scoped>
.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.swatch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.9rem;
  height: 1.9rem;
  margin: 0;
  border: 2px solid transparent;
  border-radius: 50%;
  background: var(--tag-hue);
  color: #fff;
  cursor: pointer;
}

.swatch.is-selected,
.swatch:focus-within {
  border-color: var(--color-text);
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
</style>
