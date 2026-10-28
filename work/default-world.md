# Scope: one canonical 3D game

Issue #24, branch `codex/default-world`, following user approval on 2026-10-27 to make the world the main path and merge the PRs. Replace the root game's board choice with the approved world. Remove preview labels and alternate-mode navigation. Keep `/world/` only as a compatibility redirect preserving query/hash/session identity. Use `/` for invites, new games and gallery return links. Retain automatic WebGL failure recovery as compatibility behavior, not a selectable second mode.

Acceptance: actual 3D rendering from the root route for solo and multiplayer; model UI, invitation/join, spectator, reload, completion/replay and mobile controls remain functional. Old world session URLs resume the same session. Gallery returns to the canonical game. Existing fallback tests explicitly disable WebGL; successful default tests must not silently exercise fallback. Inspect desktop/mobile captures and run the full offline gate. Merge the approved stacked PRs with ancestry preserved, then the canonical-route change, and verify master CI.

## Assessment

Full `bash scripts/agent-verify.sh` passed: 92 backend tests, 18 browser workflows, 3 physics checks, contracts/build and 58 original artwork hashes. PostgreSQL tests (19) require the CI service and were skipped locally. Normal tests now launch software WebGL globally and assert both multiplayer clients actually render 3D; fallback-only tests explicitly deny WebGL. Added old-URL query/hash/seat recovery, spectator rendering, absence of the selector, and gallery return navigation coverage. All 23 cast cards are checked for scroll reachability at 320px.

Inspected desktop world and crowded mobile captures. Raised mobile camera controls to clear the wrapping drag hint. The cancellation workflow exposed a fake-reply race with software WebGL, including at 2s on CI. A test-only provider now holds the first cancellation-scenario attempt until cancelled, then lets retry complete normally. The cancellation screenshot is captured after cancellation succeeds. Production providers/timing are unchanged. An interrupted targeted run left temporary servers orphaned; those exact test processes were stopped before the successful full run. No live model calls or migrations were needed.

PRs #14, #19, #21 and #23 merged into master in order, with merge commits retaining ancestry. Master at `8273171` is the parent of this final canonical-route increment. Hardware/browser performance outside headless Chromium remains a playtest check.
