import { onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'
import { useRoute } from 'vue-router'

export function usePaginatedQuery(
  load: () => void | Promise<void>,
  options?: { search?: Ref<string>; searchDelay?: number },
) {
  const route = useRoute()
  const page = ref(Number(route.query.page) || 1)

  function goToPage(newPage: number) {
    page.value = newPage
    load()
  }

  if (options?.search) {
    const search = options.search
    const delay = options.searchDelay ?? 300
    let timer: ReturnType<typeof setTimeout> | undefined
    watch(search, () => {
      page.value = 1
      clearTimeout(timer)
      timer = setTimeout(load, delay)
    })
    onBeforeUnmount(() => clearTimeout(timer))
  }

  onMounted(load)

  return { page, goToPage }
}
