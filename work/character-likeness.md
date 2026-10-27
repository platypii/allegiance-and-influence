# Scope: recognizable 3D characters

Issue #20, following approval of the tabletop style/motion in PR #19. Branch `codex/character-likeness`, stacked on that PR. Preserve the accepted scene, movement and rules. Focus on Einstein, Curie and Churchill, then improve the default gathering's silhouettes and costumes. Use original art for style and historical portraits for identity; preserve all existing raster files.

Acceptance: distinct head/body proportions, hair and costume profiles; hero inspection with rotating front/three-quarter views and normal board-scale captures; unchanged picking, motion, reduced motion, fallback and offline game completion. Browser/geometry checks establish rendering and behavior, not human recognition. The resulting authored geometry remains stylized procedural art, not final sculpted/rigged assets. No new cast members or paid model calls in this increment.

Reference review: original character illustrations were inspected for the established style. Historical reference images were inspected separately: Einstein's 1947 Halsman portrait (Philippe Halsman Archive, reproduced by Fuorisalone), Churchill's Karsh portrait (Smithsonian National Portrait Gallery NPG.93.145), and Curie's Wellcome Library portrait M0002559. These research images remain ignored local artifacts and are not shipped as assets. Curie's dark pinned-up hair/high collar and Churchill's stockier proportions intentionally follow historical references rather than copying the stylized original portraits literally.

## Assessment

`bash scripts/agent-verify.sh` passed: 92 backend tests, 16 browser workflows, 3 physics checks, contracts, static production build and all 58 original asset hashes. The 19 PostgreSQL tests require the CI service and were skipped locally. The new browser workflow cycles every revised figure, captures hero front/three-quarter views, checks 320px overflow and recovers from context loss by choosing another figure. Existing actual canvas picking, full-match persistence/replay, motion controls, crowded mobile and no-WebGL checks still pass. No paid model calls were used.

Inspected final desktop board, Curie front, Churchill three-quarter and 320px Einstein gallery captures under `artifacts/screenshots/`. The first inspection exposed a false context-loss fallback on character switching; each new renderer now receives a fresh keyed canvas. Revised Einstein hair into pointed locks, exposed Curie's forehead and removed an isolated Churchill chin shape after visual review.

More detailed geometry increases rendering work. The existing default-board draw-call ceiling of 400 remains enforced and passes; headless software WebGL is not a mobile hardware performance measurement. Human recognition and art direction still need playtest judgment, and the remaining 16 characters retain the earlier designs. `/characters/` returns HTTP 200 on the current Tailscale preview.
