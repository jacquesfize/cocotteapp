<script setup lang="ts">
import { useId } from 'vue'
import type { Locale } from '../i18n'

// Drapeaux en SVG plutôt qu'en emoji : Windows n'affiche pas les emojis drapeaux (il montre "FR").
defineProps<{ code: Locale }>()

// Le drapeau peut apparaître plusieurs fois sur la page (bouton + menu) : ids de clipPath uniques.
const uid = useId()
</script>

<template>
  <svg v-if="code === 'fr'" viewBox="0 0 3 2" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <rect width="1" height="2" fill="#002654" />
    <rect x="1" width="1" height="2" fill="#fff" />
    <rect x="2" width="1" height="2" fill="#ce1126" />
  </svg>
  <svg v-else viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <clipPath :id="`${uid}-t`">
      <path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z" />
    </clipPath>
    <rect width="60" height="30" fill="#012169" />
    <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6" />
    <path d="M0,0 L60,30 M60,0 L0,30" :clip-path="`url(#${uid}-t)`" stroke="#c8102e" stroke-width="4" />
    <path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10" />
    <path d="M30,0 v30 M0,15 h60" stroke="#c8102e" stroke-width="6" />
  </svg>
</template>
