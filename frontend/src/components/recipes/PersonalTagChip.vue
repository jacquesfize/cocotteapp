<script setup lang="ts">
import type { PersonalTag } from '../../types/models'
import { tagHueStyle } from '../../utils/personalTags'

// Pastille d'une étiquette personnelle, à sa couleur (voir .personal-tag dans base.css). Le slot
// accueille un éventuel bouton de retrait.
defineProps<{
  tag: Pick<PersonalTag, 'name' | 'emoji' | 'color'>
}>()
</script>

<template>
  <span class="personal-tag" :style="tagHueStyle(tag.color)">
    <span v-if="tag.emoji" aria-hidden="true">{{ tag.emoji }}</span>{{ tag.name }}<slot />
  </span>
</template>
