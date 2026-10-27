/** Faction colors share the semantic palette in globals.css. */
export function teamColor(team: number) {
  const red = [164, 60, 56]
  const neutral = [129, 120, 106]
  const blue = [49, 94, 133]
  const target = team < 0 ? red : blue
  const weight = Math.min(1, Math.abs(team))
  return `rgb(${neutral.map((value, i) => Math.round(value * (1 - weight) + target[i] * weight)).join(",")})`
}
