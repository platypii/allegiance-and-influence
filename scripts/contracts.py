#!/usr/bin/env python3
"""Generate or check API schemas and prove the validator rejects bad commands."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from game.models import COMMAND_ADAPTER, GameView  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    schemas = {
        "command": COMMAND_ADAPTER.json_schema(),
        "game-view": GameView.model_json_schema(by_alias=True),
    }
    for name, schema in schemas.items():
        path = ROOT / f"schemas/{name}-v1.schema.json"
        text = json.dumps(schema, indent=2) + "\n"
        if args.write:
            path.write_text(text)
        elif path.read_text() != text:
            raise SystemExit(f"Schema drift: {path.name}; run .venv/bin/python scripts/contracts.py --write")
        Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schemas["command"])
    for path in sorted((ROOT / "tests/fixtures/command").glob("*.json")):
        errors = list(validator.iter_errors(json.loads(path.read_text())))
        if path.stem.startswith("invalid-"):
            expected = path.stem.removeprefix("invalid-")

            # Discriminated union wraps failures; inspect its nested reasons.
            def rules(items):
                return {e.validator for e in items} | {r for e in items for r in rules(e.context)}

            if expected not in rules(errors):
                raise SystemExit(f"Failing-fixture proof failed: {path.name} did not reject {expected}")
        elif errors:
            raise SystemExit(f"Valid fixture rejected: {path.name}: {errors[0].message}")
    print(
        "PASS: schemas match runtime; valid fixtures accepted; invalid fixtures rejected for expected rules"
    )


if __name__ == "__main__":
    main()
