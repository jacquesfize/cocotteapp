import client from './client'
import type { ImageCreditInput } from './recipes'
import type { Cookware } from '../types/models'

// Liste courte, non paginée côté API : renvoie toute la bibliothèque (ou les résultats de `search`).
// `is_verified: false` : file de revue des administrateurs (matériel créé par des utilisateurs).
export function listCookware(params: { search?: string; is_verified?: boolean } = {}): Promise<Cookware[]> {
  return client.get('cookware/', { params }).then((r) => r.data)
}

export function createCookware(payload: Pick<Cookware, 'name'> & Partial<Cookware>): Promise<Cookware> {
  return client.post('cookware/', payload).then((r) => r.data)
}

export function updateCookware(id: number, payload: Partial<Cookware>): Promise<Cookware> {
  return client.patch(`cookware/${id}/`, payload).then((r) => r.data)
}

export function deleteCookware(id: number) {
  return client.delete(`cookware/${id}/`)
}

// Réservé au staff : fusionne le matériel `id` dans `into` (les recettes basculent sur la cible,
// puis `id` est supprimé). Renvoie le matériel cible.
export function mergeCookware(id: number, into: number): Promise<Cookware> {
  return client.post(`cookware/${id}/merge/`, { into }).then((r) => r.data)
}

// Même contrôle de licence et de crédit que pour une photo de recette (sans la note libre).
export function uploadCookwareImage(
  id: number,
  file: File,
  credit: Omit<ImageCreditInput, 'image_credit_note'>,
): Promise<Cookware> {
  const body = new FormData()
  body.append('image', file)
  for (const [key, value] of Object.entries(credit)) {
    if (value) body.append(key, value)
  }
  return client.patch(`cookware/${id}/image/`, body).then((r) => r.data)
}

export function removeCookwareImage(id: number): Promise<Cookware> {
  return client.delete(`cookware/${id}/image/`).then((r) => r.data)
}
