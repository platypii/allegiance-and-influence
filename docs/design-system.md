# Allegiance & Influence design system

The visual direction is a historical strategy salon: warm ivory paper, dark green framing, brass detail, and the existing expressive character portraits. The interface should feel calm enough to read an entire conversation. Faction color communicates allegiance; it does not decorate unrelated controls.

The executable source is `frontend/app/globals.css`. Open `/design-system/` on any running game server for a reference page with palette, typography, and control states. Component CSS modules handle layouts; new interface work should use the shared tokens rather than reintroducing separate palettes or font stacks.

## Tokens and hierarchy

| Purpose | Token / value | Usage |
| --- | --- | --- |
| Main ink | `--ink` / #243c35 | Text and primary controls |
| Deep ink | `--ink-strong` / #172c26 | Surrounding frame and landing background |
| Secondary ink | `--ink-muted` / #59645b | Supporting descriptions and metadata |
| Paper | `--paper` / #f6f1e6 | Main surfaces |
| Raised paper | `--paper-raised` / #fffcf5 | Forms, messages, session controls |
| Sunken paper | `--paper-sunken` / #eae4d6 | Page background, quiet status areas |
| Brass / gold | `--brass` / #886323; `--gold` / #e6c889 | Small accents, dark-surface labels |
| Factions | `--red` / #a43c38; `--blue` / #315e85 | Score labels, portrait rings, player messages |
| Focus | `--focus` / #1b6885 | Visible 3px keyboard focus outline |
| Spacing | `--space-1` through `--space-7` | 4, 8, 12, 16, 24, 32, 48px rhythm |
| Corners | `--radius-small` / 6.4px; `--radius` / 12px | Controls and panels |

Display headings and the dialogue panel use locally bundled **Lora** (variable 400–700), with Georgia as a fallback. The transcript and composer use 18px Lora with generous line spacing. General interface controls use the platform sans-serif stack. The actual font file, pinned source revision and SIL Open Font License are included under `frontend/public/fonts/lora/`; there are no third-party runtime font requests. Use rem-based body sizes to respect user font settings.

- General body/form/button text: at least **16px**. Dialogue messages and composer: **18px** Lora, 1.7/1.6 line height.
- Secondary labels, supporting metadata, character names: at least **14px**.
- Dialog/section headings: 26–36px; landing masthead scales from 38–78px.
- Primary/secondary buttons are normally 48px tall; compact dismiss/profile controls are at least 44px.
- Keep text on solid surfaces. Do not place instructions over detailed artwork or use embedded image lettering as the app title.
- Pair faction colors with written Red / Blue / Unaligned labels. Do not dim portraits merely because they cannot currently be selected.

## Layout and components

**Setup:** a portrait composition and real-text masthead beside a paper form on desktop. Stack into ordinary document flow on phones; vertical scrolling is intentional. Labels sit above full-width form fields. Characters and rounds share a row and stack when enlarged text needs more room.

**Board:** a stable score header, a separate board surface, and a sidebar for round/session controls. Mobile places those sections in document flow. The animated swarm is part of the entertainment: retain organic wandering, repulsion and pair attraction on desktop and mobile. A responsive grid seeds the positions, then presentation-only physics moves the portraits. Resolve collisions using the whole label/button rectangle; clamp to the board and keep the previous safe frame if a crowded layout cannot resolve a step. Pairing lines follow the moving portraits. Pause motion while a target is hovered, focused or pressed so it can be selected reliably. Original artwork fills the board at full opacity with only a 10% ivory tint. Keep the scenery clearly visible; use small solid paper backings behind character/faction labels instead of fading the entire illustration.

**Conversation:** a native modal dialog with a strong identity header, expandable character profile, readable message cards, and clear message/finish controls. Desktop uses a right-hand panel with a light, unblurred backdrop so the animated board remains visible; phones use the available viewport. Native dialog behavior keeps keyboard focus inside, makes the board inert, supports Escape, and restores focus to a still-focusable trigger when dismissed. Avoid autofocus on the text field so opening a profile does not immediately summon the phone keyboard. API errors belong inside the open dialog.

**Round and results:** expose the current round as a clear heading and the recap in a disclosure. Outcomes use real text and existing portraits; controls lead to the final board/replay or another match. Replay uses the same readable surfaces and labels as the live board.

**Motion:** animate the board by default, with a visible pause/resume control. Respect reduced motion, including changes while the page is open; hidden tabs must not advance the simulation. No pulsing status or glowing text. Original raster assets remain unchanged; improvements come from composition, framing, contrast, and HTML/CSS typography.

## 3D world direction

The optional `/world/` preview uses actual 3D geometry for the island, scenery and animated character maquettes while retaining the same typography, readable HTML dialogue, faction colors and original portraits. The illustrated board remains available. See [the visual world plan](visual-world-plan.md) for the production art standard, animation stages and larger cast pipeline. Procedural maquettes establish the direction; they are not final rigged character assets.

## Verification

Normal-motion tests sample actual frames for movement, collisions, bounds and interaction pauses; simulation checks cover sustained movement and pair attraction. A browser font test inspects rendered glyphs to prove Lora is used, rather than merely declared in CSS. Browser coverage also includes 320/390/430px layouts, enlarged text, a complete mobile conversation and replay, character profile access, dialog focus and Escape, and reachability of all 23 character targets. Existing desktop multiplayer, model, invite, cancellation/retry and reload workflows remain required. Inspect captures in `artifacts/screenshots/`; compare the preserved baseline in `artifacts/design-before/`. Run `bash scripts/agent-verify.sh` and retain all 58 original asset hashes.

Automated viewport checks do not substitute for testing an actual iPhone/Android keyboard or screen reader. Check both during hosted playtesting. Update this document and the reference page when introducing new components or tokens.
