import client from './client'
import type { PersonalTag } from '../types/models'

export type PersonalTagInput = Pick<PersonalTag, 'name'> & Partial<Pick<PersonalTag, 'emoji' | 'color'>>

// Étiquettes de l'utilisateur connecté uniquement ; liste courte, non paginée côté API.
export function listPersonalTags(): Promise<PersonalTag[]> {
  return client.get('personal-tags/').then((r) => r.data)
}

export function createPersonalTag(payload: PersonalTagInput): Promise<PersonalTag> {
  return client.post('personal-tags/', payload).then((r) => r.data)
}

export function updatePersonalTag(id: number, payload: Partial<PersonalTagInput>): Promise<PersonalTag> {
  return client.patch(`personal-tags/${id}/`, payload).then((r) => r.data)
}

export function deletePersonalTag(id: number) {
  return client.delete(`personal-tags/${id}/`)
}

/** Étiquettes existantes proches de `name` (accents, pluriel, faute de frappe), à proposer avant
 * d'en créer une nouvelle. `exclude` écarte l'étiquette en cours de renommage. */
export function findSimilarPersonalTags(name: string, exclude?: number): Promise<PersonalTag[]> {
  const params = exclude ? { name, exclude } : { name }
  return client.get('personal-tags/similar/', { params }).then((r) => r.data)
}
