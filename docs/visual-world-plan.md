# From readable interface to a living game world

User direction, 2026-10-25: keep the illustrated caricature style, substantially raise visual quality, make most world objects 3D, expand the cast, and make the result entertaining. The visual slice is tracked in #17; cast production in #18. The user approved the theatrical tabletop direction and its motion on 2026-10-26; character likeness is the next priority.

## The experience

An unlikely gathering of big personalities on a little world. The board is a place: a warm stone plaza, a canal, trees, lamps, pennants and miniature landmarks. Characters should look at each other, move into conversations, gesture, disagree and celebrate. Influence should be visible through reactions, faction markers and changed relationships. Keep the original expressive proportions and warm palette. Text remains clear HTML, with Lora dialogue, rather than becoming tiny labels baked into a 3D texture.

The user approved the world as the main game experience on 2026-10-27. `/` now opens the 3D gathering for all ordinary play, invitations and replay. The board-mode selector and preview labels are removed; `/world/` is only a compatibility redirect retaining query/hash. Automatic illustrated fallback remains for unavailable/lost WebGL. Most visible scene objects are actual meshes. The current 23-character library remains the playable cast, with seven figures receiving the first authored likeness pass. Production rigs and proposed cast additions below remain future work.

## Production sequence

| Stage | Concrete deliverable | Exit evidence |
| --- | --- | --- |
| 1. Playable visual slice | One complete 3D gathering, camera controls, selectable maquettes, idle/talk motion, faction feedback, readable roster and working conversations | Actual rendered desktop/mobile captures; canvas picking; a complete scripted match; pause/reduced-motion and non-WebGL fallback; existing offline gate |
| 2. Establish the final character standard | Finish Einstein, Curie and Churchill as three hero miniatures; sculpted silhouettes, coherent materials, facial features and props; shared animation skeleton with idle, walk, listen, talk, disagree and recruit clips | Turntables at game camera distance; readable silhouettes on a phone; no clipping; an actual discussion and recruitment scene that is enjoyable to watch |
| 3. Make the world respond | Conversation staging, facing/approach motion, gesture timing, localized influence trails, recruitment/victory reactions, optional sound with mute | Players can identify who is talking and who changed allegiance without reading a log; effects remain comprehensible with reduced motion |
| 4. Expand the cast in packs | First six new personas with consistent portraits, meshes, clips and motivations; then convert the remaining existing cast | Each member is selectable and has a complete content/art bundle; saved games and mixed-model assignments still work; dialogue comparisons reveal different behavior |
| 5. Mobile polish and delivery | Measured quality tiers, asset compression, loading treatment, camera/selection refinement and real-device keyboard checks | Profile on representative iPhone and Android hardware; record sustained frame time, memory, loading and thermal behavior, rather than inferring performance from desktop emulation |

Suggested first historical pack: **Ada Lovelace, Nikola Tesla, Cleopatra, Harriet Tubman, Sun Tzu and Oscar Wilde**. They offer contrasting conversation hooks: imagination and collaboration, invention and recognition, diplomacy and sovereignty, trust and collective freedom, patience and strategy, wit and convention. These are fictionalized game interpretations. They need review, not numeric claims about the real people's psychology. If the user prefers original personalities, use a parallel pack of an idealistic inventor, pragmatic diplomat, skeptical archivist, charismatic organizer, opportunistic merchant and theatrical critic.

More characters in the library does not mean more characters in every match. Keep a readable active cast (initially 6–10), with larger rosters as an experiment setting. Later add a cast picker and themed gatherings. Do not change the canonical roster, its hard-coded bounds or model-profile validation piecemeal: the content increment must update API schemas/fixtures, setup options, portraits and saved-game tests together.

## Renderer and asset boundary

Three.js is a local client dependency, loaded only when the 3D board is mounted. It projects server game state; it never decides scores, allegiance or legal targets. React continues to own setup, dialogue, controls and a keyboard-accessible character roster. Rendering failure/context loss returns the player to the illustrated board without discarding the session. Keep the current artwork intact as reference material and fallback.

Use GLB/glTF for production meshes and animation clips. Keep an independent visual manifest keyed by stable character UID, containing asset paths, portrait path, asset version, clip names, visual scale and provenance/license. Model-provider routing remains separate. A missing production asset can use a clearly identified maquette until the pack is complete. Do not bake API credentials, provider selection or experiment outcomes into assets.

For each production asset retain the editable source, exported GLB, texture sources, license/provenance and rendered review images. Aim for a small shared material palette, reusable props and a shared rig; authored character differences belong in silhouette, proportions, expressions and costume. Commissioned or generated meshes require cleanup, retopology, rigging and animation review before being called production-ready.

The slice batches immobile geometry by material, caps pixel ratio at 1.5 and animation drawing at 30 fps, stops drawing unchanged paused/reduced-motion scenes, and disposes scene resources when switching boards. These are implementation limits, not proof of mobile frame rate. Initial production budgets to validate: about 10–20k triangles per hero, shared 1k textures where practical, under 300 draw calls for an ordinary gathering, and a separately measured low-quality tier. Revisit budgets against real devices, especially 23-character experiments.

Technical basis: [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer) requires WebGL 2; [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader) supports glTF 2.0 assets and animation data. [Responsive rendering guidance](https://threejs.org/manual/pages/responsive.html) explains the cost of drawing-buffer resolution. This is why the scene has a non-WebGL fallback, explicit resolution limits and a replaceable asset boundary.

## What would make it fun

Graphics make the world inviting; conversations need choices and consequences to sustain play. After the visual slice is reviewed, test character-specific motives, a limited number of commitments, and visible reactions to arguments. Start with a single short match and observe whether players understand their options, enjoy watching the other characters, and want another round. Keep experimental controls explicit: presentation improvements must not quietly change persuasion rules or model comparisons.

## Approved direction and first likeness pass — 2026-10-26

The user approved the tabletop style and animation and asked to improve character identity (#20). Seven figures now have individually authored proportions and silhouettes: Einstein, Curie, Churchill, Mandela, Napoleon, King and Genghis Khan. `/characters/` provides a rotating close-up of the same meshes used on the board. It makes visual review possible without starting a model conversation or changing a saved game's cast.

The hero references were the original game portraits plus historical photographs: [Einstein, Halsman Archive exhibition](https://www.fuorisalone.it/it/magazine/focus/article/1288/roma-retrospettiva-italiana-philippe-halsman), [Churchill, Smithsonian National Portrait Gallery](https://npg.si.edu/object/npg_NPG.93.145), and [Curie, Wellcome Library M0002559](https://commons.wikimedia.org/wiki/File:Portrait_of_Marie_Curie_(1867_-_1934),_Polish_chemist_Wellcome_M0002559.jpg). Reference photos are not redistributed in the game. This pass changes actual geometry, not portrait textures pasted onto faces. Human review is still the test of recognition; it does not complete production sculpting, rigging or the cast-expansion milestone.
