import { markOwned } from '../api/shopping'
import { clearQueue, listQueuedWrites, queueWrite, removeQueuedWrite } from './db'

export const QUEUE_FLUSHED_EVENT = 'cocotte:queue-flushed'

// Un échec de requête axios sans `response` n'a jamais atteint le serveur (coupure
// réseau, timeout...) : c'est le seul cas où l'on met l'action de côté pour plus tard.
// Une vraie erreur serveur (400, 403...) ne doit pas être mise en file, elle ne
// deviendra pas valide en la rejouant.
export function isNetworkError(error: unknown): boolean {
  return Boolean(error) && !(error as { response?: unknown }).response
}

export async function queueMarkOwned(shoppingListId: number | string, ingredientIds: number[]) {
  await queueWrite({ type: 'mark-owned', shoppingListId, ingredientIds })
}

export async function isMarkOwnedQueued(
  shoppingListId: number | string,
  ingredientId: number,
): Promise<boolean> {
  const pending = await listQueuedWrites()
  return pending.some(
    (entry) =>
      entry.type === 'mark-owned' &&
      entry.shoppingListId === shoppingListId &&
      entry.ingredientIds.includes(ingredientId),
  )
}

// Rejoue les écritures en attente dans l'ordre, s'arrête à la première qui échoue
// encore (pas de retries en rafale tant que le réseau ne répond pas vraiment).
export async function flushQueue() {
  const pending = await listQueuedWrites()
  let flushedAny = false
  for (const entry of pending) {
    try {
      if (entry.type === 'mark-owned') {
        await markOwned(entry.shoppingListId, entry.ingredientIds)
      }
      await removeQueuedWrite(entry.id)
      flushedAny = true
    } catch (error) {
      if (isNetworkError(error)) break
      await removeQueuedWrite(entry.id)
    }
  }
  if (flushedAny) {
    window.dispatchEvent(new CustomEvent(QUEUE_FLUSHED_EVENT))
  }
}

export function setupAutoSync() {
  window.addEventListener('online', flushQueue)
}

// Sur un appareil partagé, le cache Workbox de l'agenda/des listes de courses (et la
// file d'écritures en attente) ne doivent pas survivre à un changement de compte.
export async function clearPrivateOfflineData() {
  await clearQueue().catch(() => {})
  if ('caches' in window) {
    await caches.delete('cocotte-user-data').catch(() => {})
  }
}
