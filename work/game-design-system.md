# Scope: game design system and mobile readability

Issue [#13](https://github.com/platypii/allegiance-and-influence/issues/13), under epic #1. User feedback: inconsistent fonts/CSS/text graphics and small mobile text. Work on `codex/game-design-system`; preserve character/board assets and all game/API behavior. Previous hosting PR #12 merged as `2663df9`.

## Plan

Create shared semantic tokens and reusable visual conventions. Use a historical strategy direction: ivory paper, dark green ink, brass accents, clear serif headings and system sans-serif controls. Replace tiny lettering embedded in splash art with real responsive text and compose existing portraits as the visual identity. Establish setup, board, chat, round recap, results and replay layouts. Mobile prioritizes a readable character grid and conversation, with accessible character details and controls. No new raster assets or external font dependencies.

## Acceptance

Body and form text at least 16px; secondary text at least 14px; touch controls at least 44px. No horizontal overflow at 320, 390, or 430px. Keyboard focus visible, reduced motion respected. A mobile player can choose a character, read biography/stats, send messages, complete a match and replay. Retain two-player and model flows. Verify screenshots and the full offline gate, including all original artwork hashes.

## Assess / resolve

Implemented shared semantic tokens and the `/design-system/` reference page, with written guidance in `docs/design-system.md`. Setup, lobby, board, session controls, character profiles, conversation/recovery states, round recap, result and replay now share typography and surfaces. The title/result lettering is real HTML text; all original raster assets are untouched. The decorative force layout was replaced by stable portrait positions after review found collisions; desktop relationship lines follow measured portrait centers. Native dialogs provide focus containment and Escape, with profile access on mobile and API errors inside the dialog.

The full offline verifier passed: **92 backend tests**, **8 browser workflows**, contracts/fixture failure proof, lint, frontend build/types, all **58 original artwork hashes**, clean server logs and whitespace. PostgreSQL checks remain a separate CI job step and are skipped by the offline gate. Added coverage includes 320/390/430px setup, 200% text at 320px, readable 16px inputs/messages, 44px targets, native dialog focus/Escape, a full mobile solo conversation/result/replay, and reachability without overlap for all 23 character targets.

Inspected desktop setup, board, chat, result and design reference; mobile setup, profile, chat (390×844 and 320×568), results/replay; enlarged-text setup. Original captures are in ignored `artifacts/design-before/`, new captures in `artifacts/screenshots/design-*` and refreshed numbered files. Primary text/paper palette contrast computes to 10.52:1, secondary text/paper 5.49:1, and faction score colors at least 5.05:1. This is a palette check, not a claim of a complete accessibility audit.

Verification found and resolved a model-mode lobby label regression, enlarged caption overflow, and static subpage routing (Next directory-index export now serves `/design-system/`). No live inference or backend/API changes. Real-device iOS/Android keyboard and screen-reader playtesting and Replit publishing remain outside this local implementation.

## User review correction: motion and dialogue type

Issue [#15](https://github.com/platypii/allegiance-and-influence/issues/15). The user explicitly rejected removing board animation: it is part of the entertainment. They also rejected the plain Arial-like dialogue text. Supersedes the stable-board/system-font choice above. Restore organic motion and pair attraction with measured label collision bounds, pointer/keyboard target stability, pause and reduced-motion behavior. Bundle Lora locally with its license and verify the loaded font rather than relying on a system fallback. Assess normal-motion recordings and browser checks separately from reduced-motion captures.


### Correction evidence

Restored continuous wandering, repulsion, faction gravity and pair attraction in presentation-only physics. Measured full portrait/label bounds stay separate; targets steady on mouse hover, pointer interaction and keyboard focus. Added explicit pause/resume and live reduced-motion handling. Desktop chat uses a light, unblurred backdrop. Lora is bundled unmodified with its OFL license/source; dialogue and composer use 18px type.

The full offline gate passed after the correction: **92 backend tests, 11 browser workflows and 3 physics checks**, plus lint, contracts, build/types, all **58 artwork hashes**, server logs and whitespace. Browser tests sample actual animation frames on desktop and a 25-portrait mobile board, check interaction pauses, and inspect browser-rendered glyphs to confirm custom Lora. Pure simulations check a minute of safe continuous motion and pair attraction. Inspected final desktop/mobile Lora dialogue and displaced swarm captures; a normal-motion video was captured as additional review evidence in ignored `artifacts/swarm-video/`. No paid model calls or backend changes.

CI exposed an intermittent live reduced-motion transition: repeated reads of `MediaQueryList.matches` from the animation loop could suppress its change event in Chromium. A local instrumented reproduction showed the updated query value with no event. The loop now uses the cached event value. Both directions of preference changes are covered; eight repeated browser motion tests and 30 consecutive preference transitions passed after the fix.

## User review correction: visible board scenery

Issue [#16](https://github.com/platypii/allegiance-and-influence/issues/16). The original board graphic was nearly invisible under combined 18% opacity and a radial paper wash. Remove both the heavy fade and elliptical crop; fill the board with the original illustration and only a 10% ivory tint. Solid paper label backings preserve text readability. Acceptance: inspect desktop/mobile captures, preserve animation/target behavior and original asset hashes, and pass the offline verifier.

Verified the visibility correction with the full offline gate: 92 backend tests, 11 browser workflows, 3 physics checks and all 58 original artwork hashes passed. Inspected refreshed desktop board, desktop conversation backdrop and mobile board captures: scenery is clearly visible and labels remain readable.
