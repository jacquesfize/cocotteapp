<script setup lang="ts">
import { FlaskConical, Sparkles, Wrench, X } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { listAnnouncements } from '../../api/announcements'
import type { Announcement } from '../../types/models'

const { locale, t } = useI18n()

const STORAGE_KEY = 'dismissed-announcements'
const announcements = ref<Announcement[]>([])
const dismissed = ref<Record<string, string>>(readDismissed())

function readDismissed(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}')
  } catch {
    return {}
  }
}

// Une annonce modifiée (updated_at différent) réapparaît même si elle avait été fermée.
function version(a: Announcement) {
  return a.updated_at ?? ''
}

const visible = computed(() =>
  announcements.value.filter((a) => !(a.dismissible && dismissed.value[String(a.id)] === version(a))),
)

function pick(a: Announcement, field: 'title' | 'message' | 'link_label') {
  const fr = a[`${field}_fr` as 'title_fr'] ?? ''
  const en = a[`${field}_en` as 'title_en'] ?? ''
  return (locale.value === 'en' ? en || fr : fr || en).trim()
}

function content(a: Announcement) {
  if (a.id === 'test-instance') {
    return { title: t('announcement.testInstance.title'), message: t('announcement.testInstance.message'), label: '' }
  }
  return { title: pick(a, 'title'), message: pick(a, 'message'), label: pick(a, 'link_label') }
}

// Le lien vient du Django admin : on n'accepte qu'un chemin du site ou une URL http(s), jamais `javascript:` ou `data:`.
function safeLink(a: Announcement) {
  const url = (a.link_url ?? '').trim()
  return /^(\/(?!\/)|https?:\/\/)/i.test(url) ? url : ''
}

const ICONS = { info: Sparkles, warning: FlaskConical, critical: Wrench }

function dismiss(a: Announcement) {
  dismissed.value = { ...dismissed.value, [String(a.id)]: version(a) }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dismissed.value))
  } catch {
    // Stockage indisponible (navigation privée...) : la fermeture ne vaut que pour cette page.
  }
}

onMounted(async () => {
  try {
    announcements.value = await listAnnouncements()
  } catch {
    // Une annonce est un confort : jamais d'erreur affichée si l'API ne répond pas.
  }
})
</script>

<template>
  <div v-if="visible.length" class="announcements">
    <div
      v-for="a in visible"
      :key="a.id"
      class="announcement"
      :class="`announcement--${a.level}`"
      :role="a.level === 'critical' ? 'alert' : 'status'"
    >
      <component :is="ICONS[a.level]" :size="18" class="announcement__icon" aria-hidden="true" />
      <p class="announcement__text">
        <strong v-if="content(a).title">{{ content(a).title }}</strong>
        {{ content(a).message }}
        <a v-if="safeLink(a) && content(a).label" :href="safeLink(a)" class="announcement__link">{{
          content(a).label
        }}</a>
      </p>
      <button
        v-if="a.dismissible"
        type="button"
        class="announcement__close"
        :aria-label="$t('announcement.dismiss')"
        @click="dismiss(a)"
      >
        <X :size="18" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.announcements {
  /* Déplie le bandeau une seule fois à l'arrivée, sans effet pour qui préfère moins d'animations. */
  animation: announcement-unfold 0.35s ease-out;
}

@keyframes announcement-unfold {
  from {
    max-height: 0;
    opacity: 0;
  }
  to {
    max-height: 20rem;
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .announcements {
    animation: none;
  }
}

.announcement {
  /* Neutre (pas la teinte de l'accent, trop proche du rouge de « critique »), seule l'icône colorée. */
  --tone: var(--color-primary-dark);
  --tone-bg: var(--color-surface-muted);
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  /* Fond pleine largeur, contenu aligné sur la colonne de .container (960px, gouttière 1rem). */
  padding: 0.6rem max(1rem, calc((100% - 960px) / 2 + 1rem));
  background: var(--tone-bg);
  color: var(--color-text);
  border-bottom: 1px solid color-mix(in srgb, var(--tone) 25%, transparent);
  font-size: 0.9rem;
  line-height: 1.45;
}

.announcement--warning {
  --tone: var(--color-carbon-medium);
  --tone-bg: color-mix(in srgb, var(--color-carbon-medium) 16%, var(--color-surface));
}

.announcement--critical {
  --tone: var(--color-danger);
  --tone-bg: var(--color-danger-soft);
}

.announcement__icon {
  flex-shrink: 0;
  margin-top: 0.15rem;
  color: var(--tone);
}

.announcement__text {
  flex: 1;
  margin: 0;
  max-width: 70ch;
}

.announcement__link {
  margin-left: 0.25rem;
  color: var(--color-text);
  font-weight: 600;
  text-underline-offset: 2px;
}

.announcement__close {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  /* Zone tactile de 44px sans agrandir visuellement le bandeau. */
  width: 44px;
  height: 44px;
  margin: -0.65rem -0.75rem -0.65rem 0;
  border: 0;
  background: transparent;
  color: var(--color-muted);
  border-radius: var(--radius-pill);
  cursor: pointer;
}

.announcement__close:hover {
  color: var(--color-text);
}

.announcement__close:focus-visible,
.announcement__link:focus-visible {
  outline: 2px solid var(--tone);
  outline-offset: 2px;
}
</style>
