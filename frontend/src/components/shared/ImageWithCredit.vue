<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { imageCreditDomain, imageLicenseLabelKey } from '../../utils/imageCredit'

// Composant d'affichage partagé pour une image de recette ou d'étape + sa ligne de crédit.
// Couvre 4 cas (voir docs/user-guide/creating-recipes.md#credit-and-license) :
// 1. Licence renseignée (hors "unknown") : "Photo : {auteur}" + lien(s) source/licence.
// 2. Licence "unknown" (import automatique depuis une URL) avec une note : la note telle quelle.
// 3. Aucune licence persistée (image d'avant cette fonctionnalité) mais une `source_url` : on
//    retombe sur l'ancien comportement (domaine de la source, voir utils/imageCredit.ts).
// 4. Image sans aucune info de crédit : libellé neutre "Crédit non précisé".
const props = withDefaults(
  defineProps<{
    imageUrl?: string | null
    sourceUrl?: string | null
    license?: string | null
    creditAuthor?: string | null
    creditSourceUrl?: string | null
    creditLicenseUrl?: string | null
    creditNote?: string | null
    alt?: string
    imgClass?: string
    // Légende courte, tronquée sur une ligne, sans liens (miniatures/listes).
    compact?: boolean
    // Légende affichée en pastille superposée au coin de l'image plutôt qu'en dessous
    // (tuiles, carrousel, bannière recette restreinte).
    overlay?: boolean
    overlayAlign?: 'left' | 'right'
  }>(),
  { overlayAlign: 'left' },
)

const { t } = useI18n()

const isLicensed = computed(() => Boolean(props.license) && props.license !== 'unknown')

const licenseLabel = computed(() => {
  const key = imageLicenseLabelKey(props.license)
  return key ? t(key) : ''
})

// Texte de base (sans liens) : utilisé tel quel en mode compact/overlay, et comme préfixe du
// rendu enrichi (avec liens) sinon.
const creditText = computed(() => {
  if (isLicensed.value) {
    return props.creditAuthor ? t('imageCredit.photoBy', { author: props.creditAuthor }) : licenseLabel.value
  }
  if (props.license === 'unknown' && props.creditNote) return props.creditNote
  if (!props.license) {
    const domain = imageCreditDomain(props.sourceUrl)
    if (domain) return t('recipes.imageCredit', { domain })
  }
  return props.imageUrl ? t('imageCredit.notSpecified') : ''
})

const showLinks = computed(
  () => !props.compact && !props.overlay && isLicensed.value && (props.creditSourceUrl || props.creditLicenseUrl),
)
</script>

<template>
  <div v-if="imageUrl" class="image-with-credit" :class="{ overlay }">
    <div class="image-with-credit-frame">
      <img :src="imageUrl" :class="imgClass" :alt="alt || ''" loading="lazy" />
      <slot />
      <span v-if="overlay && creditText" class="credit-badge" :class="overlayAlign">{{ creditText }}</span>
    </div>
    <p v-if="!overlay && creditText" class="image-credit-line muted" :class="{ compact }">
      <template v-if="showLinks">
        {{ creditText }}
        <template v-if="creditSourceUrl">
          ·
          <a :href="creditSourceUrl" target="_blank" rel="noopener noreferrer">{{ $t('recipes.source') }}</a>
        </template>
        <template v-if="creditLicenseUrl">
          ·
          <a :href="creditLicenseUrl" target="_blank" rel="noopener noreferrer">{{ licenseLabel }}</a>
        </template>
      </template>
      <template v-else>{{ creditText }}</template>
    </p>
  </div>
</template>

<style scoped>
.image-with-credit-frame {
  position: relative;
}

.image-with-credit-frame img {
  display: block;
  width: 100%;
  height: 100%;
}

.credit-badge {
  position: absolute;
  bottom: 0.75rem;
  padding: 0.25rem 0.65rem;
  border-radius: var(--radius-pill);
  background: rgba(0, 0, 0, 0.55);
  color: var(--color-on-primary);
  font-size: 0.7rem;
  max-width: calc(100% - 1.5rem);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.credit-badge.left {
  left: 0.75rem;
}

.credit-badge.right {
  right: 0.75rem;
}

.image-credit-line {
  margin: 0.35rem 0 0;
  font-size: 0.78rem;
}

.image-credit-line.compact {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-credit-line a {
  color: inherit;
  text-decoration: underline;
}
</style>
