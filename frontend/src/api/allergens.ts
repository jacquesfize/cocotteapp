import client from './client'
import type { Allergen } from '../types/models'

export function listAllergens(): Promise<Allergen[]> {
  return client.get('allergens/').then((r) => r.data)
}
