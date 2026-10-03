import { onBeforeUnmount, onMounted, type Ref } from 'vue'
import { isEmbedHeightMessage } from '../utils/embedMessages'

/** Grows each embedded recipe iframe under `root` to the height its content reports (see
 * RecipeEmbedView.vue). Only same-origin messages from one of those iframes are honoured. */
export function useEmbedAutoHeight(root: Ref<HTMLElement | null | undefined>) {
  function handleMessage(event: MessageEvent) {
    if (event.origin !== window.location.origin || !isEmbedHeightMessage(event.data)) return
    const iframes = root.value?.querySelectorAll<HTMLIFrameElement>('iframe[data-cocotte-recipe]') ?? []
    for (const iframe of iframes) {
      if (iframe.contentWindow === event.source) {
        iframe.style.height = `${Math.ceil(event.data.height)}px`
      }
    }
  }

  onMounted(() => window.addEventListener('message', handleMessage))
  onBeforeUnmount(() => window.removeEventListener('message', handleMessage))
}
