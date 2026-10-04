import { onBeforeUnmount, ref, watch, type WatchSource } from 'vue'
import { i18n } from '../i18n'

export const APP_NAME = 'Cocotte'

// Clé i18n du titre de la route courante (meta.title), posée par le hook afterEach du routeur.
const routeTitleKey = ref<string | undefined>()
// Titre explicite posé par une vue une fois ses données chargées (titre d'une recette, d'un
// article) : prioritaire sur meta.title.
const viewTitle = ref<string | null>(null)

export function formatDocumentTitle(page: string | null | undefined): string {
  return page ? `${page} · ${APP_NAME}` : APP_NAME
}

function applyDocumentTitle() {
  const page = viewTitle.value || (routeTitleKey.value ? i18n.global.t(routeTitleKey.value) : '')
  document.title = formatDocumentTitle(page)
}

// Réévalue le titre au changement de langue, de route ou de titre de vue.
watch([routeTitleKey, viewTitle, () => i18n.global.locale.value], applyDocumentTitle)

/** Appelé par le routeur après chaque navigation. */
export function setRouteTitle(key: string | undefined) {
  routeTitleKey.value = key
  viewTitle.value = null
  applyDocumentTitle()
}

/**
 * Remplace le titre générique de la route par un titre propre à la vue (ex. le titre d'une
 * recette) dès qu'il est connu ; on retombe sur meta.title tant qu'il est vide.
 */
export function usePageTitle(source: WatchSource<string | null | undefined>) {
  watch(
    source,
    (title) => {
      viewTitle.value = title || null
    },
    { immediate: true },
  )
  onBeforeUnmount(() => {
    viewTitle.value = null
  })
}
