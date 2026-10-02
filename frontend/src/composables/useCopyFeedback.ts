import { onBeforeUnmount, ref } from 'vue'

export function useCopyFeedback(resetDelay = 2000) {
  const copied = ref(false)
  let timer: ReturnType<typeof setTimeout> | undefined

  async function copy(text: string) {
    await navigator.clipboard.writeText(text)
    copied.value = true
    clearTimeout(timer)
    timer = setTimeout(() => {
      copied.value = false
    }, resetDelay)
  }

  onBeforeUnmount(() => clearTimeout(timer))

  return { copied, copy }
}
