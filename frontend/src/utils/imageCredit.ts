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

/** Les 6 licences d'image acceptées par l'API (`Recipe.image_license` / `RecipeStep.image_license`). */
export type ImageLicense = 'cc_by' | 'cc_by_sa' | 'public_domain' | 'personal' | 'permission' | 'unknown'

export const IMAGE_LICENSES: ImageLicense[] = [
  'cc_by',
  'cc_by_sa',
  'public_domain',
  'personal',
  'permission',
  'unknown',
]

/** Clé i18n du libellé humain de chaque licence (voir locales `imageLicense.*`). */
export function imageLicenseLabelKey(license: string | null | undefined): string {
  const map: Record<string, string> = {
    cc_by: 'imageLicense.ccBy',
    cc_by_sa: 'imageLicense.ccBySa',
    public_domain: 'imageLicense.publicDomain',
    personal: 'imageLicense.personal',
    permission: 'imageLicense.permission',
    unknown: 'imageLicense.unknown',
  }
  return license && map[license] ? map[license] : ''
}

/** URL par défaut du texte de la licence, pré-remplie (mais éditable) quand l'utilisateur choisit
 * une licence CC — le serveur applique le même défaut si le champ est laissé vide. */
export function defaultLicenseUrl(license: string | null | undefined): string {
  if (license === 'cc_by') return 'https://creativecommons.org/licenses/by/4.0/'
  if (license === 'cc_by_sa') return 'https://creativecommons.org/licenses/by-sa/4.0/'
  return ''
}

/** Champs de crédit requis pour chaque licence, en miroir de la validation serveur
 * (voir apps/recipes/serializers.py) : le formulaire ne doit demander/valider que ceux-ci. */
export function requiredCreditFields(
  license: string | null | undefined,
): Array<'creditAuthor' | 'creditSourceUrl' | 'creditNote'> {
  switch (license) {
    case 'cc_by':
    case 'cc_by_sa':
      return ['creditAuthor', 'creditSourceUrl']
    case 'personal':
      return ['creditAuthor']
    case 'permission':
      return ['creditAuthor', 'creditNote']
    default:
      return []
  }
}
