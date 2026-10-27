# Scope: drag the 3D board

Issue #22, branch `codex/drag-board`, stacked on PR #21. Add direct mouse rotation and bounded vertical tilt to the shared 3D renderer, with grab/grabbing feedback. Preserve click selection, touch page scrolling/taps, animation, pause/reduced motion and button controls. No game-rule, model, artwork or dependency changes.

Plan: distinguish clicks from drags with a small movement threshold; capture the pointer so release outside the canvas terminates cleanly; clear gesture state on cancellation, lost capture, window blur and disposal. Verify real camera movement while animation is paused, including drag from a character without recruitment, return-to-origin drag suppression, normal clicks and portrait dragging. Inspect board capture and run the full offline verifier.

## Assessment

Full `bash scripts/agent-verify.sh` passed: 92 backend tests, 17 browser workflows, 3 physics checks, contracts/build and all 58 original artwork hashes. PostgreSQL checks are CI-only locally (19 skipped). The new workflow tests horizontal rotation and vertical tilt with idle animation disabled, drag from a selectable figure, return-to-origin suppression, release outside the canvas, pointer cancellation/lost capture/window blur, and normal picking afterward. The portrait workflow verifies dragging changes its rendered mesh view. Existing motion, buttons, mobile layout, full-match/replay and fallback workflows also pass.

Inspected `artifacts/screenshots/world-dragged.png`: the island rotates and tilts with the characters still visible and controls reachable. Mouse dragging is deliberate; touch retains page scrolling and tap selection. No inference calls or dependencies were added.
