import client from './client'
import type { FreeImageSuggestion, ImportPreview } from '../types/models'

export function previewImportFromUrl(url: string): Promise<ImportPreview> {
  return client.post('import/url/', { url }).then((r) => r.data)
}

export function suggestFreeImages(query: string): Promise<FreeImageSuggestion[]> {
  return client.get('import/image-suggestions/', { params: { q: query } }).then((r) => r.data.results)
}
