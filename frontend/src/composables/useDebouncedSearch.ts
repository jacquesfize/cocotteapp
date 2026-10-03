import { onBeforeUnmount, ref, type Ref } from 'vue'

export function useDebouncedSearch<T>(
  fetcher: (query: string) => Promise<T[]>,
  options?: { delay?: number; onResults?: (results: T[]) => void },
) {
  const results = ref<T[]>([]) as Ref<T[]>
  const delay = options?.delay ?? 250
  let timer: ReturnType<typeof setTimeout> | undefined
  let latestQuery = ''

  function cancel() {
    clearTimeout(timer)
  }

  function clear() {
    cancel()
    results.value = []
  }

  function search(query: string) {
    cancel()
    latestQuery = query
    timer = setTimeout(async () => {
      const data = await fetcher(query)
      // Ignore a response for a query that's no longer current (e.g. a slower earlier
      // request resolving after a newer one).
      if (query !== latestQuery) return
      results.value = data
      options?.onResults?.(data)
    }, delay)
  }

  onBeforeUnmount(cancel)

  return { results, search, cancel, clear }
}
