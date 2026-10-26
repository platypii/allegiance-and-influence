import * as THREE from "three"
import { batch, box, cylinder, sphere, solid, type Paint } from "./geometry"
import { characterSculpt } from "./sculpts"
export { palette, solid } from "./geometry"

type Look = { skin: string; coat: string; hair: string; hat?: "top" | "bicorne" | "crown" | "fur"; glasses?: boolean; wild?: boolean; beard?: boolean; dress?: boolean; bald?: boolean; mustache?: boolean }
const looks: Record<string, Partial<Look>> = {
  albert_einstein: { coat: "#a49374", hair: "#ebe7d8", wild: true, mustache: true },
  winston_churchill: { coat: "#354a4e", hat: "top", bald: true },
  marie_curie: { coat: "#275a60", hair: "#61452e", dress: true },
  nelson_mandela: { skin: "#895b3e", coat: "#d7ad58", hair: "#b9b7a2" },
  martin_luther: { skin: "#a56d48", coat: "#3e555e", mustache: true },
  napoleon_bonaparte: { coat: "#284d69", hat: "bicorne" },
  genghis_khan: { skin: "#c18c5e", coat: "#724c32", hat: "fur", beard: true },
  mahatma_gandhi: { skin: "#b88554", coat: "#f0dfb8", bald: true, glasses: true, dress: true },
  mother_teresa: { coat: "#ecdfc7", hair: "#e2e6dc", dress: true },
  rosa_parks: { skin: "#a36d4c", coat: "#a66b65", glasses: true, dress: true },
  queen_elizabeth: { coat: "#8e4851", hair: "#a34c32", hat: "crown", dress: true },
  margaret_thatcher: { coat: "#426c97", hair: "#d2a46a", dress: true },
  leonardo_davinci: { coat: "#91483c", hair: "#d5cec0", beard: true },
  julius_caesar: { coat: "#e6d9ba", hair: "#66503a", hat: "crown", dress: true },
  william_shakespeare: { coat: "#705276", hair: "#6d4b32", beard: true },
  steve_jobs: { coat: "#344144", bald: true, glasses: true },
  bill_gates: { coat: "#687c87", glasses: true, hair: "#a28865" },
  gary_marcus: { coat: "#687166", glasses: true },
  hunter_s_thompson: { coat: "#d7bc86", glasses: true, bald: true },
  donald_trump: { coat: "#344e72", hair: "#e5bc75" },
  mao_zedong: { coat: "#657461", hair: "#38403b" },
  player_red: { coat: "#b94f44", hair: "#754631", glasses: true },
  player_blue: { coat: "#437fa0", hair: "#403d37", glasses: true },
}

export function miniature(id: string, paint: Paint) {
  const sculpt = characterSculpt(id, paint)
  if (sculpt) return sculpt
  const look: Look = { skin: "#e3b486", coat: "#536c6b", hair: "#514436", ...looks[id] }
  const figure = new THREE.Group()
  const { skin, coat, hair } = look
  // Large heads, tiny feet and tactile clothing echo the original caricatures.
  sphere(figure, paint, "#343c38", -.19, .16, .08, .21, .13, .3)
  sphere(figure, paint, "#343c38", .19, .16, .08, .21, .13, .3)
  cylinder(figure, paint, coat, 0, .61, 0, .28, look.dress ? .52 : .37, .8)
  if (!look.dress) {
    box(figure, paint, "#eee0be", 0, .87, .28, .19, .33, .04)
    box(figure, paint, "#a55645", 0, .83, .32, .06, .28, .04)
  }
  for (const side of [-1, 1]) {
    const sleeve = sphere(figure, paint, coat, side * .37, .72, 0, .15, .34, .17)
    sleeve.rotation.z = side * .15
    sphere(figure, paint, skin, side * .42, .43, .06, .14)
    sphere(figure, paint, skin, side * .48, 1.43, 0, .12, .17, .1)
  }
  sphere(figure, paint, skin, 0, 1.46, .015, .5, .53, .43)
  sphere(figure, paint, skin, 0, 1.4, .45, .115, .13, .1)
  for (const side of [-1, 1]) {
    sphere(figure, paint, "#fff3db", side * .185, 1.55, .404, .125, .145, .055)
    sphere(figure, paint, "#293b37", side * .17, 1.54, .455, .059, .076, .035)
    sphere(figure, paint, "#ffffff", side * .15, 1.57, .48, .018)
    const brow = box(figure, paint, hair, side * .19, 1.75, .37, .22, .055, .06)
    brow.rotation.z = side * -.1
    if (look.glasses) {
      solid(figure, new THREE.TorusGeometry(.151, .019, 6, 24), paint("#805f35", .5), side * .19, 1.55, .48)
    }
  }
  if (look.glasses) box(figure, paint, "#805f35", 0, 1.56, .49, .1, .026, .03)
  const smile = solid(figure, new THREE.TorusGeometry(.12, .018, 6, 16, Math.PI * .7), paint("#94624c"), 0, 1.27, .423)
  smile.rotation.z = Math.PI * 1.15
  if (!look.bald) {
    for (let i = 0; i < (look.wild ? 13 : 9); i++) {
      const a = i / (look.wild ? 12 : 8) * Math.PI
      sphere(figure, paint, hair, Math.cos(a) * .42, 1.72 + Math.sin(a) * .23, -.07, look.wild ? .22 : .17, look.wild ? .17 : .19, .31)
    }
  } else {
    for (const side of [-1, 1]) sphere(figure, paint, hair, side * .43, 1.59, -.13, .08, .2, .24)
  }
  if (look.mustache) for (const side of [-1, 1]) sphere(figure, paint, hair, side * .1, 1.31, .46, .13, .055, .055)
  if (look.beard) sphere(figure, paint, hair, 0, 1.14, .26, .34, .25, .25)
  if (look.hat === "top") {
    cylinder(figure, paint, "#2b3d3d", 0, 1.91, 0, .6, .6, .08)
    cylinder(figure, paint, "#2b3d3d", 0, 2.11, 0, .39, .43, .38)
    cylinder(figure, paint, "#93794e", 0, 1.98, 0, .434, .44, .08)
  }
  if (look.hat === "bicorne") {
    sphere(figure, paint, "#253b41", 0, 1.98, 0, .75, .29, .31)
    box(figure, paint, "#d7af57", 0, 2.1, .28, .15, .18, .06)
  }
  if (look.hat === "crown") {
    cylinder(figure, paint, "#dfb760", 0, 1.99, 0, .42, .42, .16)
    for (let i = 0; i < 7; i++) {
      const a = i / 7 * Math.PI * 2
      cylinder(figure, paint, "#dfb760", Math.cos(a) * .39, 2.13, Math.sin(a) * .39, 0, .07, .25, 6)
    }
  }
  if (look.hat === "fur") {
    sphere(figure, paint, "#7b6043", 0, 1.95, 0, .55, .22, .44)
    cylinder(figure, paint, "#bc9857", 0, 2.16, 0, .03, .18, .34, 8)
  }
  // Distinct props, rather than a shared recolored capsule.
  if (id === "marie_curie") {
    sphere(figure, paint, "#7ecb9c", .52, .56, .2, .17, .2, .17)
    cylinder(figure, paint, "#d8e9d3", .52, .79, .2, .06, .07, .16)
  }
  if (id === "albert_einstein") {
    const book = box(figure, paint, "#50776b", -.5, .53, .19, .23, .39, .17)
    book.rotation.z = -.2
  }
  if (id === "winston_churchill") cylinder(figure, paint, "#8c5b35", .48, .5, .22, .03, .03, .27, 8).rotation.x = 1.2
  batch(figure)
  return figure
}

export function scenery(paint: Paint) {
  const group = new THREE.Group()
  // Layered wood and brass plinth, land, canal, promenade and central plaza.
  cylinder(group, paint, "#334b43", 0, -.66, 0, 10.4, 10.1, .75, 96)
  cylinder(group, paint, "#bf9455", 0, -.28, 0, 10.45, 10.45, .13, 96)
  cylinder(group, paint, "#526e55", 0, -.05, 0, 10.1, 10.4, .4, 96)
  cylinder(group, paint, "#529f9d", 0, .18, 0, 9.62, 9.62, .1, 96)
  cylinder(group, paint, "#a1b979", 0, .25, 0, 8.55, 8.6, .19, 96)
  cylinder(group, paint, "#e0c28c", 0, .36, 0, 6.85, 7.05, .24, 64)
  cylinder(group, paint, "#f1d8a3", 0, .5, 0, 6.46, 6.55, .12, 64)
  // Inlaid compass and paving segments.
  for (let i = 0; i < 64; i++) {
    const a = i / 64 * Math.PI * 2
    const tile = box(group, paint, i % 2 ? "#c7a779" : "#dfc89a", Math.cos(a) * 6.7, .49, Math.sin(a) * 6.7, .53, .12, .4)
    tile.rotation.y = -a
  }
  const compass = solid(group, new THREE.RingGeometry(1.1, 1.14, 64), paint("#cfad70"), 0, .565, 0)
  compass.rotation.x = -Math.PI / 2
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * Math.PI * 2
    const mark = box(group, paint, "#c5a466", Math.sin(a) * .65, .568, Math.cos(a) * .65, .04, .008, .65)
    mark.rotation.y = a
  }
  function tree(x: number, z: number, scale: number, color: string) {
    cylinder(group, paint, "#96764b", x, .65, z, .08 * scale, .12 * scale, .85 * scale, 8)
    sphere(group, paint, color, x, .8 + .6 * scale, z, .55 * scale, .75 * scale, .55 * scale)
    sphere(group, paint, "#91a96b", x - .16 * scale, 1 + .7 * scale, z + .08, .3 * scale, .45 * scale, .3 * scale)
  }
  for (let i = 0; i < 34; i++) {
    const a = i / 34 * Math.PI * 2
    const r = 7.7 + .35 * Math.sin(i * 2.7)
    tree(Math.cos(a) * r, Math.sin(a) * r, .6 + (i % 4) * .13, i % 2 ? "#607f52" : "#728f5b")
  }
  // A clock tower, domed academy and columned salon evoke the illustrated map.
  for (const [x, z, scale, roof] of [[-5.8, -5.9, 1.15, "#487a79"], [5.6, -5.9, .9, "#b6784b"], [-8.1, .3, .7, "#527a79"], [8.1, .1, .65, "#b6784b"]] as const) {
    box(group, paint, "#ead5ad", x, .4 + scale, z, 1.35 * scale, 2 * scale, 1.25 * scale)
    box(group, paint, "#c8ab7b", x, .45, z, 1.65 * scale, .3, 1.55 * scale)
    for (const level of [.9, 1.65]) for (const side of [-1, 1]) {
      box(group, paint, "#496567", x + side * .33 * scale, .4 + level * scale, z + .635 * scale, .22 * scale, .42 * scale, .04)
    }
    const roofMesh = cylinder(group, paint, roof, x, .4 + 2.35 * scale, z, 0, 1.02 * scale, .75 * scale, 4)
    roofMesh.rotation.y = Math.PI / 4
    if (x === -5.8) {
      box(group, paint, "#dfc494", x, 3.7, z, .88, 1.8, .8)
      cylinder(group, paint, roof, x, 4.85, z, 0, .73, .9, 4).rotation.y = Math.PI / 4
      const clock = cylinder(group, paint, "#f5e8c5", x, 3.95, z + .43, .29, .29, .06, 24)
      clock.rotation.x = Math.PI / 2
      box(group, paint, "#665535", x, 4.02, z + .48, .035, .2, .03)
      box(group, paint, "#665535", x + .06, 3.95, z + .48, .15, .035, .03)
    }
  }
  box(group, paint, "#ddc79d", 0, .55, -7.55, 3.6, .5, 1.8)
  for (let i = 0; i < 6; i++) cylinder(group, paint, "#f2dfb8", -1.4 + i * .56, 1.55, -6.85, .12, .15, 1.7, 12)
  box(group, paint, "#ebd8b1", 0, 2.43, -7.45, 3.7, .26, 1.9)
  sphere(group, paint, "#58918a", 0, 2.55, -7.45, 1.45, .93, .85)
  cylinder(group, paint, "#ccab65", 0, 3.56, -7.45, 0, .15, .4, 12)
  // Four little bridges across the canal.
  for (let i = 0; i < 4; i++) {
    const a = i / 4 * Math.PI * 2 + Math.PI / 4
    const bridge = box(group, paint, "#dfba80", Math.cos(a) * 9.05, .42, Math.sin(a) * 9.05, 1.55, .16, 1.05)
    bridge.rotation.y = -a
    for (const sign of [-1, 1]) {
      const rail = box(group, paint, "#b08954", Math.cos(a) * 9.05 + Math.sin(a) * sign * .49, .68, Math.sin(a) * 9.05 - Math.cos(a) * sign * .49, 1.55, .1, .08)
      rail.rotation.y = -a
    }
  }
  // Lamps and pennants give the gathering a sense of occasion.
  for (const x of [-6.6, 6.6]) for (const z of [-2.6, 2.6]) {
    cylinder(group, paint, "#486058", x, 1.3, z, .045, .065, 2.1, 8)
    sphere(group, paint, "#ffe0a0", x, 2.42, z, .19, .23, .19)
    cylinder(group, paint, "#486058", x, 2.67, z, 0, .25, .23, 6)
  }
  for (const side of [-1, 1]) {
    cylinder(group, paint, "#a78851", side * 7.3, 1.65, 4.1, .04, .065, 2.7, 10)
    box(group, paint, side < 0 ? "#b95748" : "#497f9a", side * 7.3 + .42, 2.53, 4.1, .82, .55, .035)
    sphere(group, paint, "#e3be70", side * 7.3, 3.05, 4.1, .085)
  }
  batch(group)
  return group
}
