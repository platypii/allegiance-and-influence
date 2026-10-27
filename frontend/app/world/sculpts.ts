import * as THREE from "three"
import { batch, box, cylinder, solid, sphere, type Paint } from "./geometry"

// Identity comes from proportions and silhouettes before small surface details.
// These seven authored designs replace the shared face/body maquette.
export const sculptedCharacters = ["albert_einstein", "marie_curie", "winston_churchill", "napoleon_bonaparte", "nelson_mandela", "martin_luther", "genghis_khan"] as const
type Face = { skin: string; hair: string; width: number; height: number; jaw: number; eyes: number; brow: number; nose: number; smile: number; age?: boolean }

function stroke(group: THREE.Group, paint: Paint, color: string, points: number[][], thickness = .018) {
  return solid(group, new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p))), 12, thickness, 6, false), paint(color))
}
function ellipsoid(group: THREE.Group, paint: Paint, color: string, x: number, y: number, z: number, sx: number, sy: number, sz: number, tilt = 0) {
  const mesh = sphere(group, paint, color, x, y, z, sx, sy, sz)
  mesh.rotation.z = tilt
  return mesh
}
function hairLock(group: THREE.Group, paint: Paint, color: string, points: number[][], radius: number) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)))
  const geometry = new THREE.TubeGeometry(curve, 12, radius, 8, false)
  const position = geometry.getAttribute("position")
  for (let ring = 0; ring <= 12; ring++) {
    const t = ring / 12, center = curve.getPointAt(t), taper = Math.pow(1 - t, .65)
    for (let edge = 0; edge <= 8; edge++) {
      const i = ring * 9 + edge
      position.setXYZ(i, center.x + (position.getX(i) - center.x) * taper, center.y + (position.getY(i) - center.y) * taper, center.z + (position.getZ(i) - center.z) * taper)
    }
  }
  geometry.computeVertexNormals()
  solid(group, geometry, paint(color))
}
function face(group: THREE.Group, paint: Paint, f: Face) {
  const geometry = new THREE.SphereGeometry(1, 28, 20)
  const positions = geometry.getAttribute("position")
  for (let i = 0; i < positions.count; i++) {
    const x = positions.getX(i), y = positions.getY(i), z = positions.getZ(i)
    const jaw = y < 0 ? 1 + f.jaw * Math.sin(-y * Math.PI) : 1
    positions.setXYZ(i, x * f.width * jaw, 1.58 + y * f.height, z * .42)
  }
  geometry.computeVertexNormals()
  solid(group, geometry, paint(f.skin))
  for (const side of [-1, 1]) {
    ellipsoid(group, paint, f.skin, side * f.width * .96, 1.52, -.005, .09, .14, .085)
    const ex = side * f.width * .39
    ellipsoid(group, paint, "#fff0d9", ex, 1.62, .378, .122, f.eyes, .06)
    ellipsoid(group, paint, "#3c352b", ex - side * .01, 1.61, .433, .052, f.eyes * .8, .028)
    ellipsoid(group, paint, "#121d1b", ex - side * .01, 1.61, .456, .029, f.eyes * .6, .012)
    sphere(group, paint, "#ffffff", ex - .015, 1.632, .465, .014)
    stroke(group, paint, f.skin, [[ex - .12, 1.63, .405], [ex, 1.62 + f.eyes, .425], [ex + .12, 1.63, .405]], .024)
    stroke(group, paint, f.hair, [[ex - side * .12, 1.76 + f.brow, .39], [ex, 1.78, .405], [ex + side * .12, 1.76 - f.brow, .365]], .025)
  }
  ellipsoid(group, paint, f.skin, 0, 1.5, .43, f.nose * .65, .155, .085)
  ellipsoid(group, paint, f.skin, 0, 1.425, .5, f.nose, .085, .08)
  stroke(group, paint, "#9b6654", [[-.14, 1.285 + f.smile, .34], [0, 1.285, .39], [.14, 1.285 + f.smile, .34]], .014)
  if (f.age) {
    for (const y of [1.89, 1.95]) stroke(group, paint, "#c29c7d", [[-.25, y, .295], [0, y + .018, .34], [.25, y, .295]], .008)
    for (const side of [-1, 1]) stroke(group, paint, "#bd9477", [[side * .3, 1.48, .32], [side * .31, 1.4, .32], [side * .25, 1.32, .33]], .009)
  }
}
function shoes(group: THREE.Group, paint: Paint, spacing = .18) {
  for (const side of [-1, 1]) {
    cylinder(group, paint, "#303536", side * spacing, .22, 0, .12, .14, .23, 16)
    ellipsoid(group, paint, "#29302f", side * spacing, .1, .1, .18, .105, .29)
  }
}
function suit(group: THREE.Group, paint: Paint, color: string, width: number, bow = false, sleeves = color) {
  shoes(group, paint, width * .5)
  ellipsoid(group, paint, color, 0, .63, 0, width, .48, .31)
  box(group, paint, "#ece5cf", 0, .94, .255, width * .7, .29, .07)
  for (const side of [-1, 1]) {
    // Long tapered lapels read as a jacket at board distance.
    ellipsoid(group, paint, color, side * .16, .86, .28, .1, .25, .035, -side * .42)
    ellipsoid(group, paint, sleeves, side * (width + .015), .71, 0, .14, .33, .17, side * .16)
    ellipsoid(group, paint, "#e0b18b", side * (width + .055), .43, .07, .12, .12, .11)
  }
  if (bow) {
    for (const side of [-1, 1]) ellipsoid(group, paint, "#263532", side * .08, .97, .325, .085, .055, .035, side * .12)
    sphere(group, paint, "#263532", 0, .97, .34, .04)
  } else box(group, paint, "#944c42", 0, .86, .325, .065, .23, .035)
  for (const y of [.68, .53]) sphere(group, paint, "#bcab83", .025, y, .315, .022)
}
function spectacles(group: THREE.Group, paint: Paint, width = .205, round = true) {
  for (const side of [-1, 1]) {
    const rim = solid(group, new THREE.TorusGeometry(.15, .022, 7, 28), paint("#303a37"), side * width, 1.62, .478)
    if (!round) rim.scale.set(1.13, .87, 1)
    stroke(group, paint, "#303a37", [[side * (width + .15), 1.64, .47], [side * .47, 1.63, .12]], .019)
  }
  stroke(group, paint, "#303a37", [[-.055, 1.64, .49], [0, 1.67, .5], [.055, 1.64, .49]], .016)
}
function hairCap(group: THREE.Group, paint: Paint, color: string, width: number, height: number, short = false) {
  // Spherical cap sits on the cranium, avoiding the old identical row of curls.
  const mesh = solid(group, new THREE.SphereGeometry(1, 24, 12, 0, Math.PI * 2, 0, short ? 1.08 : 1.05), paint(color), 0, 1.58, -.025)
  mesh.scale.set(width + .025, height + .04, .45)
  const back = solid(group, new THREE.SphereGeometry(1, 16, 12, Math.PI, Math.PI, 0, 1.65), paint(color), 0, 1.58, -.025)
  back.scale.set(width + .025, height + .04, .45)
}

function einstein(group: THREE.Group, paint: Paint) {
  suit(group, paint, "#3f4e50", .34, false, "#e6dfc9")
  face(group, paint, { skin: "#e0b38d", hair: "#d8d6c9", width: .48, height: .54, jaw: -.08, eyes: .07, brow: .015, nose: .105, smile: .018, age: true })
  // Open forehead, wind-swept side wings and asymmetrical pointed locks.
  for (const side of [-1, 1]) {
    ellipsoid(group, paint, "#deded0", side * .43, 1.85, -.14, .17, .23, .3, -side * .2)
    for (let i = 0; i < 7; i++) {
      const y = 1.65 + i * .067
      hairLock(group, paint, i % 2 ? "#eeeeDF" : "#d8d9ce", [[side * .42, y, -.04], [side * .59, y + .07, .01], [side * (.68 + (i % 3) * .035), y + .14 + (i % 2) * .04, -.06]], .105)
    }
    // Drooping bushy moustache in the lower face, not a thin painted line.
    ellipsoid(group, paint, "#e6e4d7", side * .12, 1.34, .432, .165, .085, .08, -side * .22)
  }
  for (let i = 0; i < 7; i++) {
    const x = -.3 + i * .1
    hairLock(group, paint, "#e7e7dc", [[x, 2.04, -.06], [x + .04, 2.17, -.04], [x + .07, 2.25 + (i % 3) * .035, -.1]], .09)
  }
  box(group, paint, "#826447", -.46, .52, .15, .18, .34, .13).rotation.z = -.2
}
function curie(group: THREE.Group, paint: Paint) {
  shoes(group, paint, .15)
  cylinder(group, paint, "#354e50", 0, .56, 0, .245, .44, .9, 32)
  ellipsoid(group, paint, "#354e50", 0, .91, 0, .29, .25, .24)
  for (const side of [-1, 1]) {
    ellipsoid(group, paint, "#354e50", side * .3, .77, 0, .12, .29, .14, side * .12)
    ellipsoid(group, paint, "#d9ad8b", side * .34, .51, .09, .1, .11, .1)
  }
  cylinder(group, paint, "#eee4cd", 0, 1.09, 0, .18, .21, .16, 20)
  // A pale bib and high collar, based on the period portrait.
  ellipsoid(group, paint, "#eee4cd", 0, .93, .225, .2, .2, .025)
  sphere(group, paint, "#b59a65", 0, 1.025, .257, .032)
  face(group, paint, { skin: "#d9ad8b", hair: "#594332", width: .385, height: .55, jaw: -.14, eyes: .085, brow: .02, nose: .075, smile: .005 })
  hairCap(group, paint, "#594332", .39, .55)
  ellipsoid(group, paint, "#624b36", -.18, 2.045, -.015, .28, .13, .35, .18)
  ellipsoid(group, paint, "#594332", .19, 2.035, -.05, .2, .12, .32, -.25)
  sphere(group, paint, "#594332", 0, 1.83, -.47, .23, .24, .2)
  for (let i = 0; i < 3; i++) stroke(group, paint, "#765b43", [[-.31 + i * .11, 1.97, .2], [-.2 + i * .1, 2.13, .01], [0, 2.05, -.35]], .012)
  sphere(group, paint, "#8ab9a4", .4, .52, .21, .145, .16, .145)
  cylinder(group, paint, "#d9e1cb", .4, .72, .21, .045, .06, .18, 12)
  cylinder(group, paint, "#a78b64", .4, .82, .21, .045, .045, .035, 12)
}
function churchill(group: THREE.Group, paint: Paint) {
  suit(group, paint, "#41474b", .49, true)
  face(group, paint, { skin: "#e2b895", hair: "#8e7760", width: .55, height: .46, jaw: .18, eyes: .055, brow: -.05, nose: .095, smile: -.045, age: true })
  for (const side of [-1, 1]) ellipsoid(group, paint, "#b5ad98", side * .52, 1.72, -.16, .06, .17, .22)
  // Low homburg crown and upturned brim, rather than a tall generic top hat.
  const brim = cylinder(group, paint, "#303735", 0, 2.005, -.025, .64, .62, .06, 40)
  brim.scale.z = .8
  const crown = ellipsoid(group, paint, "#303735", 0, 2.135, -.04, .46, .22, .36)
  crown.scale.y *= .9
  const band = cylinder(group, paint, "#1f2b29", 0, 2.045, -.04, .45, .47, .08, 32)
  band.scale.z = .8
  for (const side of [-1, 1]) box(group, paint, "#eee5d3", side * .055 + .26, .87, .3, .085, .12, .02).rotation.z = side * .4
  const cigar = cylinder(group, paint, "#845432", .58, .5, .21, .035, .035, .29, 12)
  cigar.rotation.x = Math.PI / 2.3
  sphere(group, paint, "#b7966f", .58, .55, .34, .035)
  stroke(group, paint, "#c4ab73", [[.04, .65, .34], [.18, .55, .32], [.3, .66, .29]], .009)
}
function napoleon(group: THREE.Group, paint: Paint) {
  suit(group, paint, "#29485f", .31)
  face(group, paint, { skin: "#e1b18a", hair: "#3c3630", width: .45, height: .48, jaw: -.04, eyes: .065, brow: -.06, nose: .075, smile: -.02 })
  hairCap(group, paint, "#3c3630", .45, .48)
  ellipsoid(group, paint, "#3c3630", -.18, 1.99, .15, .24, .09, .25, .2)
  ellipsoid(group, paint, "#263638", 0, 2.11, -.05, .77, .23, .31)
  for (const side of [-1, 1]) stroke(group, paint, "#c8a55a", [[side * .68, 2.08, .05], [side * .4, 2.23, .23], [0, 2.2, .25]], .018)
  sphere(group, paint, "#bd5146", .16, 2.15, .27, .065)
  sphere(group, paint, "#dec78d", .16, 2.15, .31, .03)
  ellipsoid(group, paint, "#a84a42", .06, .67, -.22, .4, .47, .09, -.1)
  for (const side of [-1, 1]) {
    ellipsoid(group, paint, "#d6b15f", side * .33, .98, .01, .17, .045, .19)
    for (const y of [.7, .82, .94]) sphere(group, paint, "#d6b15f", side * .1, y, .33, .025)
  }
  stroke(group, paint, "#d8cba5", [[-.23, 1.02, .27], [0, .8, .34], [.2, .56, .28]], .04)
}
function mandela(group: THREE.Group, paint: Paint, king: boolean) {
  const skin = king ? "#9b694c" : "#98684b"
  suit(group, paint, king ? "#344b57" : "#696b58", king ? .37 : .34)
  face(group, paint, { skin, hair: king ? "#302f2a" : "#c8c7b5", width: king ? .48 : .44, height: king ? .48 : .52, jaw: king ? .09 : -.04, eyes: .08, brow: .005, nose: .115, smile: king ? .005 : .045 })
  hairCap(group, paint, king ? "#302f2a" : "#c8c7b5", king ? .48 : .44, king ? .48 : .52, true)
  if (king) {
    for (const side of [-1, 1]) ellipsoid(group, paint, "#302f2a", side * .085, 1.34, .417, .095, .027, .03)
    ellipsoid(group, paint, "#302f2a", -.16, 2.025, .02, .23, .075, .3, .08)
  } else {
    spectacles(group, paint, .18, false)
    // Small patterned panels distinguish his shirt from every suited figure.
    for (const x of [-.18, .18]) for (const y of [.63, .77, .91]) {
      box(group, paint, "#bf9c61", x, y, .3, .07, .05, .02).rotation.z = Math.PI / 4
    }
  }
  // Match hands to each character's face rather than inheriting the suit default.
  for (const side of [-1, 1]) ellipsoid(group, paint, skin, side * (king ? .425 : .395), .43, .08, .125, .125, .115)
}
function khan(group: THREE.Group, paint: Paint) {
  shoes(group, paint, .24)
  cylinder(group, paint, "#465752", 0, .61, 0, .39, .51, .83, 28)
  face(group, paint, { skin: "#c9966e", hair: "#2e3432", width: .56, height: .46, jaw: .1, eyes: .055, brow: -.065, nose: .09, smile: -.025 })
  hairCap(group, paint, "#2e3432", .56, .46)
  sphere(group, paint, "#2e3432", 0, 2.17, -.1, .15, .26, .17)
  cylinder(group, paint, "#ac5441", 0, 2.05, -.1, .13, .13, .06, 16)
  for (const side of [-1, 1]) {
    ellipsoid(group, paint, "#2e3432", side * .12, 1.34, .42, .16, .04, .05, -side * .18)
    ellipsoid(group, paint, "#465752", side * .29, .81, .24, .32, .14, .16, -side * .25)
  }
  stroke(group, paint, "#c1a362", [[-.27, 1.04, .2], [.03, .83, .33], [.31, .62, .28]], .035)
  const belt = cylinder(group, paint, "#9e4e41", 0, .5, 0, .48, .48, .12, 28)
  belt.scale.z = .75
  box(group, paint, "#cfaf65", .08, .5, .37, .12, .15, .045)
}

export function characterSculpt(id: string, paint: Paint): THREE.Group | null {
  if (!(sculptedCharacters as readonly string[]).includes(id)) return null
  const group = new THREE.Group()
  if (id === "albert_einstein") einstein(group, paint)
  else if (id === "marie_curie") curie(group, paint)
  else if (id === "winston_churchill") churchill(group, paint)
  else if (id === "napoleon_bonaparte") napoleon(group, paint)
  else if (id === "genghis_khan") khan(group, paint)
  else mandela(group, paint, id === "martin_luther")
  batch(group)
  group.userData.visualVersion = "likeness-1"
  return group
}
