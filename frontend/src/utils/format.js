export function formatDuration(minutes) {
  if (!minutes) return '0 min'
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours === 0) return `${rest} min`
  if (rest === 0) return `${hours} h`
  return `${hours} h ${rest} min`
}

export const DIET_LABELS = {
  omnivore: 'Omnivore',
  vegetarian: 'Végétarien',
  vegan: 'Végan',
}

export const MEAL_TYPE_LABELS = {
  breakfast: 'Petit-déjeuner',
  lunch: 'Déjeuner',
  dinner: 'Dîner',
  snack: 'Collation',
}
