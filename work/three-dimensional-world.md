# Scope: a playable 3D tabletop direction

Issues #17 (visual slice) and #18 (cast pipeline). Branch `codex/three-dimensional-world`, stacked on the unmerged design-system PR #14. The user wants a much more attractive, entertaining game, most objects in 3D, and more characters; the existing caricature style is still welcome.

## Plan and acceptance

Build an optional `/world/` entry into the same game, using a genuinely rendered 3D diorama: raised ground, water, architectural miniatures, trees, flags, lights and character figurines. Preserve the existing illustrated board and all original artwork. The first figures are procedural art-direction models, not finished rigged production assets. Keep the existing authoritative API, selection, conversation, rounds and replay. Include camera controls, a readable character roster, reduced motion, resource cleanup and a playable fallback when WebGL is unavailable.

Verify canvas rendering and picking, a complete scripted game, faction updates, mobile layout, camera/pause behavior and WebGL failure. Inspect actual desktop/mobile captures; run the offline factory gate. No live inference is needed. Record asset-production and cast-expansion milestones separately: new names must not be presented as playable before personas and art are integrated.

## Assess / resolve

Implemented the optional `/world/` route and in-game selector, locally loaded Three.js, a batched procedural diorama and character maquettes, camera controls, target picking, idle/talk motion, faction feedback and accessible original-portrait cards. Existing conversations, rounds, saves and replay use the shared game component. Renderer failure/context loss preserves the game via the illustrated fallback. All 58 original art files remain intact. The production plan in `docs/visual-world-plan.md` separates hero art/rigging, expressive animation, cast packs and mobile profiling; the playable cast remains the existing 23.

The complete offline gate passed: **92 backend tests, 15 browser workflows, 3 physics checks**, contracts/fixtures, lint, build/types, original assets, server logs and whitespace. Four new workflows cover rendered geometry/pixels, actual canvas hit testing, two-round recruitment/completion/reload/replay, camera and motion controls, live reduced-motion changes, renderer switching, full-roster mobile selection, context loss and no-WebGL fallback. Corrected a stale initial camera projection, a test locator that used visible copy instead of the button's accessible name, and narrow-screen control/hint wrapping during verification.

Inspected desktop, zoomed/rotated camera, 390px and 320px mobile captures, including the 23-character board. A normal-motion recording is captured in ignored `artifacts/world-video/`. The default eight-figure gathering reports 291 draw calls and 190,890 submitted triangles (including shadows) in local software WebGL. Frame rate and mobile thermals have not been validated on physical hardware. No live model calls or backend/API changes. New character content and finished production rigs are follow-up #18, not implied by the prototype.
