export function getErrorStatus(err: unknown): number | undefined {
  if (typeof err !== 'object' || err === null) return undefined
  return (err as { response?: { status?: number } }).response?.status
}

export function getErrorData<T>(err: unknown): T | undefined {
  if (typeof err !== 'object' || err === null) return undefined
  return (err as { response?: { data?: T } }).response?.data
}

export function getErrorDetail(err: unknown, fallback: string): string {
  return getErrorData<{ detail?: string }>(err)?.detail || fallback
}
