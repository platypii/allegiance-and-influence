export function teamColor(team: number) {
  const red = [255, 0, 0] // -1: red
  const grey = [160, 160, 160] // 0: grey
  const blue = [0, 0, 255] // 1: blue

  // Interpolate between colors based on the value
  let color
  if (team < 0) {
    // Interpolate between red and grey
    const t = (team + 1) / 1 // Map -1 to 0, and 0 to 1
    color = red.map((c, i) => Math.round(c * (1 - t) + grey[i] * t))
  } else {
    // Interpolate between grey and blue
    const t = team // Map 0 to 0, and 1 to 1
    color = grey.map((c, i) => Math.round(c * (1 - t) + blue[i] * t))
  }

  // Return the color as a CSS rgb string
  return `rgb(${color.join(",")})`
}
