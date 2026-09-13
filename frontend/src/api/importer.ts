import client from './client'
import type { ImportPreview } from '../types/models'

export function previewImportFromUrl(url: string): Promise<ImportPreview> {
  return client.post('import/url/', { url }).then((r) => r.data)
}
