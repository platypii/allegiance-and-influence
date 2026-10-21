# Browser interface

React/Next.js renders the existing artwork and animated influence board. `gameplay/characters.json` is the shared roster. The frontend talks only to the same-origin Python server through HTTP and WebSockets.

From the repository root, run `bash scripts/setup.sh` and `bash scripts/run-local.sh`. See the root README for local and LAN multiplayer, development, and verification. Rebuild interface changes with `npm --prefix frontend run build` and reload the browser.

This project uses Next.js static export. The supported runtime serves `frontend/out/` from Python; `next start` is not used. Playwright tests run against this same built output with an isolated SQLite database.
