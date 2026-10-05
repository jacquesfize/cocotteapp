// Noms des sections d'une liste de lignes, dans l'ordre où elles apparaissent. Une liste vide n'a
// qu'une section, sans nom : la première section existe toujours (et peut rester sans nom).
export function sectionNamesOf(rows: { group_name: string }[]): string[] {
  const names: string[] = []
  for (const row of rows) {
    if (!names.includes(row.group_name)) names.push(row.group_name)
  }
  return names.length ? names : ['']
}

// Regroupe les lignes par section en gardant l'ordre relatif des lignes d'une même section.
// `sectionNames` impose l'ordre des sections (celles qui n'y figurent pas passent à la suite).
export function orderRowsBySection<T extends { group_name: string; order: number }>(
  rows: T[],
  sectionNames: string[] = sectionNamesOf(rows),
): T[] {
  const names = [...sectionNames]
  for (const row of rows) {
    if (!names.includes(row.group_name)) names.push(row.group_name)
  }
  return names
    .flatMap((name) => rows.filter((row) => row.group_name === name))
    .map((row, index) => ({ ...row, order: index + 1 }))
}
