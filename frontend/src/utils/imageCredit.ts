/** Domaine à afficher en crédit d'image ("image via <domaine>") pour une recette important une
 * image depuis sa source (`source_url`) : dérivé côté client plutôt que stocké, pour éviter un
 * champ redondant à resynchroniser si la source venait à changer. Retourne `null` si l'URL est
 * invalide ou absente, auquel cas l'appelant n'affiche simplement pas de crédit. */
export function imageCreditDomain(sourceUrl: string | null | undefined): string | null {
  if (!sourceUrl) return null
  try {
    return new URL(sourceUrl).hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}
