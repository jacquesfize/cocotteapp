import { computed, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDuration } from '../utils/format'

export type StepTimerPhase = 'idle' | 'running' | 'paused' | 'finished'

// Extrait de StepTimerButton.vue pour permettre de partager le même minuteur entre la pastille
// affichée dans le texte d'une étape et le dock du mode cuisine (RecipeCookMode.vue) : les deux
// pilotent la même instance au lieu d'en démarrer une chacun. `onBeforeUnmount` s'attache au
// composant appelant (StepTimerButton en usage autonome, RecipeCookMode quand un handle est
// partagé), donc le nettoyage reste correct dans les deux cas sans gestion manuelle.
export function useStepTimer(seconds: number, label?: string) {
  const { t } = useI18n()

  const phase = ref<StepTimerPhase>('idle')
  const remainingSeconds = ref(Math.round(seconds))
  let intervalId: ReturnType<typeof setInterval> | undefined

  // formatDuration() est pensé pour des durées de recette en minutes entières ; en dessous
  // d'une minute ou pour un reste de secondes (~{30%s}, ~{90%s}...), l'arrondir à la minute la
  // plus proche afficherait un bouton "1 min" pour un minuteur de 30 secondes, ce qui est faux.
  const durationLabel = computed(() => {
    const total = Math.round(seconds)
    if (total < 60) return t('timer.seconds', { n: total })
    if (total % 60 === 0) return formatDuration(total / 60)
    return t('timer.minutesSeconds', { m: Math.floor(total / 60), s: total % 60 })
  })

  const clockLabel = computed(() => {
    const total = Math.max(0, remainingSeconds.value)
    const h = Math.floor(total / 3600)
    const m = Math.floor((total % 3600) / 60)
    const s = total % 60
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    return `${m}:${String(s).padStart(2, '0')}`
  })

  function stopInterval() {
    if (intervalId !== undefined) {
      clearInterval(intervalId)
      intervalId = undefined
    }
  }

  function tick() {
    if (remainingSeconds.value <= 1) {
      remainingSeconds.value = 0
      stopInterval()
      phase.value = 'finished'
      playChime()
      notifyFinished()
      return
    }
    remainingSeconds.value -= 1
  }

  // Demandée au clic sur "démarrer" (geste utilisateur requis par les navigateurs) plutôt qu'au
  // montage : ne redemande rien si déjà accordée/refusée, le navigateur ne réaffiche de toute
  // façon pas la boîte de dialogue une fois la décision prise.
  function ensureNotificationPermission() {
    if (typeof Notification === 'undefined' || Notification.permission !== 'default') return
    Notification.requestPermission().catch(() => {})
  }

  function start() {
    stopInterval()
    phase.value = 'running'
    intervalId = setInterval(tick, 1000)
    ensureNotificationPermission()
  }

  function pause() {
    stopInterval()
    phase.value = 'paused'
  }

  function reset() {
    stopInterval()
    phase.value = 'idle'
    remainingSeconds.value = Math.round(seconds)
  }

  // Petit carillon généré à la volée (pas de fichier audio à charger) ; l'AudioContext doit
  // être créé après une interaction utilisateur (politique navigateur), ce qui est le cas ici
  // puisque le décompte n'a pu démarrer que via un clic sur le bouton.
  function playChime() {
    try {
      const AudioContextCtor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
      if (!AudioContextCtor) return
      const ctx = new AudioContextCtor()
      const now = ctx.currentTime
      ;[0, 0.3, 0.6].forEach((offset) => {
        const oscillator = ctx.createOscillator()
        const gain = ctx.createGain()
        oscillator.type = 'sine'
        oscillator.frequency.value = 880
        gain.gain.setValueAtTime(0.0001, now + offset)
        gain.gain.exponentialRampToValueAtTime(0.3, now + offset + 0.02)
        gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + 0.25)
        oscillator.connect(gain).connect(ctx.destination)
        oscillator.start(now + offset)
        oscillator.stop(now + offset + 0.3)
      })
    } catch {
      // Web Audio indisponible ou bloqué par le navigateur : l'état visuel "terminé" suffit.
    }
  }

  // Chrome Android (et d'autres navigateurs mobiles) refuse `new Notification()` en dehors
  // d'un service worker ("Illegal constructor") : on passe donc par le service worker de la
  // PWA (enregistré au démarrage dans main.ts) quand il est disponible, avec un court délai
  // au cas où il ne serait pas encore actif, et on ne se rabat sur le constructeur classique
  // que s'il n'y en a pas.
  async function getServiceWorkerRegistration(): Promise<ServiceWorkerRegistration | null> {
    if (!('serviceWorker' in navigator)) return null
    try {
      const registration = await Promise.race([
        navigator.serviceWorker.ready,
        new Promise<null>((resolve) => setTimeout(() => resolve(null), 1500)),
      ])
      return registration
    } catch {
      return null
    }
  }

  async function notifyFinished() {
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return

    const title = t('timer.notificationTitle')
    const body = label
      ? t('timer.notificationBodyNamed', { label, duration: durationLabel.value })
      : t('timer.notificationBody', { duration: durationLabel.value })
    const options: NotificationOptions = { body, icon: '/pwa-192.png', badge: '/pwa-192.png' }

    try {
      const registration = await getServiceWorkerRegistration()
      if (registration) {
        await registration.showNotification(title, options)
      } else {
        new Notification(title, options)
      }
    } catch {
      // Notification bloquée ou non supportée malgré la permission accordée : le carillon et
      // le badge visuel "Terminé !" restent le repli.
    }
  }

  onBeforeUnmount(stopInterval)

  return { phase, remainingSeconds, durationLabel, clockLabel, start, pause, reset }
}

export type StepTimerHandle = ReturnType<typeof useStepTimer>
