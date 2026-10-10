<script setup lang="ts">
import { Camera } from '@lucide/vue'
import { computed, ref, useId } from 'vue'
import { useI18n } from 'vue-i18n'
import { useClickOutside } from '../../composables/useClickOutside'
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
    // Crédit réduit à une petite icône appareil photo dans un coin de l'image : le texte
    // complet (jamais tronqué) s'affiche dans une bulle au survol, au focus ou au toucher, et
    // sert de libellé accessible. Pour les vignettes trop petites pour une légende lisible
    // (cartes recette en liste et en tuile) ; ne pas utiliser dans un lien (<button> imbriqué).
    infoButton?: boolean
    // Coin utilisé par la pastille `overlay` et par l'icône `infoButton`.
    overlayAlign?: 'left' | 'right'
    overlayPosition?: 'top' | 'bottom'
  }>(),
  { overlayAlign: 'left', overlayPosition: 'bottom' },
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

// Bulle du mode `infoButton` : ouverte au clic/toucher (le survol et le focus clavier sont
// gérés en CSS), refermée au clic ailleurs ou sur Échap.
const popoverId = useId()
const infoOpen = ref(false)
const infoEl = ref<HTMLElement | null>(null)
useClickOutside(infoEl, () => {
  infoOpen.value = false
})
</script>

<template>
  <div v-if="imageUrl" class="image-with-credit" :class="{ overlay }">
    <div class="image-with-credit-frame">
      <img :src="imageUrl" :class="imgClass" :alt="alt || ''" loading="lazy" />
      <slot />
      <span
        v-if="infoButton && creditText"
        ref="infoEl"
        class="credit-info"
        :class="[overlayAlign, overlayPosition, { open: infoOpen }]"
      >
        <button
          type="button"
          class="credit-info-btn"
          :aria-label="t('imageCredit.infoLabel', { credit: creditText })"
          :aria-expanded="infoOpen"
          :aria-describedby="popoverId"
          @click="infoOpen = !infoOpen"
        >
          <Camera :size="12" aria-hidden="true" />
        </button>
        <span :id="popoverId" role="tooltip" class="credit-popover">{{ creditText }}</span>
      </span>
      <span
        v-else-if="overlay && creditText"
        class="credit-badge"
        :class="[overlayAlign, overlayPosition]"
        :title="creditText"
      >{{ creditText }}</span>
    </div>
    <p v-if="!overlay && !infoButton && creditText" class="image-credit-line muted" :class="{ compact }" :title="compact ? creditText : undefined">
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

.credit-badge.bottom {
  bottom: 0.75rem;
}

.credit-badge.top {
  top: 0.75rem;
}

/* Mode `infoButton` : pastille ronde dans un coin, bulle ancrée dessus qui s'ouvre vers
   l'intérieur de l'image (vers le bas depuis un coin haut, vers le haut depuis un coin bas). */
.credit-info {
  position: absolute;
  z-index: 2;
  display: inline-flex;
}

.credit-info.left {
  left: 0.35rem;
}

.credit-info.right {
  right: 0.35rem;
}

.credit-info.top {
  top: 0.35rem;
}

.credit-info.bottom {
  bottom: 0.35rem;
}

.credit-info-btn {
  width: 1.4rem;
  min-height: 1.4rem;
  height: 1.4rem;
  padding: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  opacity: 0.85;
}

/* Cible tactile élargie sans agrandir la pastille visible. */
.credit-info-btn::before {
  content: '';
  position: absolute;
  inset: -0.5rem;
}

.credit-info-btn:hover,
.credit-info.open .credit-info-btn {
  background: rgba(0, 0, 0, 0.75);
  opacity: 1;
}

.credit-info-btn:focus-visible {
  outline: 2px solid #fff;
  outline-offset: 1px;
}

.credit-popover {
  position: absolute;
  width: max-content;
  max-width: var(--credit-popover-max-width, 15rem);
  padding: 0.3rem 0.6rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.82);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 500;
  line-height: 1.35;
  white-space: normal;
  overflow-wrap: anywhere;
  pointer-events: none;
  visibility: hidden;
  opacity: 0;
  transition: opacity 0.12s ease;
}

.credit-info.left .credit-popover {
  left: 0;
}

.credit-info.right .credit-popover {
  right: 0;
}

.credit-info.top .credit-popover {
  top: calc(100% + 0.3rem);
}

.credit-info.bottom .credit-popover {
  bottom: calc(100% + 0.3rem);
}

.credit-info:hover .credit-popover,
.credit-info:focus-within .credit-popover,
.credit-info.open .credit-popover {
  visibility: visible;
  opacity: 1;
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
