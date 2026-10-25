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
