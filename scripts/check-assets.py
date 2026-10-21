"""Verify original artwork and canonical character/portrait coverage."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "tests/fixtures/assets.json").read_text())
for name, expected in manifest.items():
    actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"Artwork changed: {name}; review the visual contract before updating the manifest")
characters = json.loads((ROOT / "gameplay/characters.json").read_text())
ids = [c["UID"] for c in characters]
assert len(ids) == len(set(ids)), "Duplicate character IDs"
for uid in [*ids, "player_red", "player_blue"]:
    assert (ROOT / f"frontend/public/images/agents/{uid}.jpg").is_file(), f"Portrait missing: {uid}"
source = (ROOT / "frontend/app/characters.ts").read_text()
assert 'from "../../gameplay/characters.json"' in source, "Frontend must use the canonical roster"
for path in (ROOT / "frontend/app").rglob("*"):
    if path.suffix in {".ts", ".tsx", ".css"}:
        text = path.read_text()
        assert "firebase" not in text.lower(), f"Cloud dependency in {path}"
        assert "fonts.googleapis.com" not in text, f"External font in {path}"
print(f"PASS: {len(manifest)} original assets intact; {len(ids)} character portraits present; local frontend")
