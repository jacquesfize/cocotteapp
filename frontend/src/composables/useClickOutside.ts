import { onBeforeUnmount, onMounted, type Ref } from 'vue'

export function useClickOutside(
  targetRef: Ref<HTMLElement | null>,
  onDismiss: () => void,
  options?: { event?: 'click' | 'mousedown'; escape?: boolean },
) {
  const eventName = options?.event ?? 'click'
  const escapeEnabled = options?.escape ?? true

  function handlePointer(event: Event) {
    if (targetRef.value && !targetRef.value.contains(event.target as Node)) {
      onDismiss()
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') onDismiss()
  }

  onMounted(() => {
    document.addEventListener(eventName, handlePointer)
    if (escapeEnabled) document.addEventListener('keydown', handleKeydown)
  })

  onBeforeUnmount(() => {
    document.removeEventListener(eventName, handlePointer)
    if (escapeEnabled) document.removeEventListener('keydown', handleKeydown)
  })
}
