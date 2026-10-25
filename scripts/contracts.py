#!/usr/bin/env python3
"""Generate or check API schemas and prove positive and negative fixtures."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from game.agent_contracts import AgentRequest, ProviderResult, RuntimeReport  # noqa: E402
from game.experiments import PairReport, PairScenario  # noqa: E402
from game.model_config import ModelConfig  # noqa: E402
from game.models import COMMAND_ADAPTER, GameView  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    schemas = {
        "command-v2": COMMAND_ADAPTER.json_schema(),
        "game-view-v3": GameView.model_json_schema(by_alias=True),
        "agent-request-v2": AgentRequest.model_json_schema(by_alias=True),
        "agent-result-v2": ProviderResult.model_json_schema(),
        "runtime-report-v2": RuntimeReport.model_json_schema(),
        "model-config-v1": ModelConfig.model_json_schema(),
        "pair-scenario-v1": PairScenario.model_json_schema(),
        "pair-report-v1": PairReport.model_json_schema(by_alias=True),
    }
    for name, schema in schemas.items():
        path = ROOT / f"schemas/{name}.schema.json"
        text = json.dumps(schema, indent=2) + "\n"
        if args.write:
            path.write_text(text)
        elif path.read_text() != text:
            raise SystemExit(f"Schema drift: {path.name}; run .venv/bin/python scripts/contracts.py --write")
        Draft202012Validator.check_schema(schema)
    for directory, schema_name in [
        ("command", "command-v2"),
        ("game-view", "game-view-v3"),
        ("agent-request", "agent-request-v2"),
        ("agent-result", "agent-result-v2"),
        ("runtime-report", "runtime-report-v2"),
        ("model-config", "model-config-v1"),
        ("pair-scenario", "pair-scenario-v1"),
        ("pair-report", "pair-report-v1"),
    ]:
        validator = Draft202012Validator(schemas[schema_name])
        fixtures = sorted((ROOT / "tests/fixtures" / directory).glob("*.json"))
        if not any(p.stem.startswith("invalid-") for p in fixtures) or not any(
            p.stem.startswith("valid-") for p in fixtures
        ):
            raise SystemExit(f"Missing positive or negative contract fixtures: {directory}")
        for path in fixtures:
            errors = list(validator.iter_errors(json.loads(path.read_text())))
            if path.stem.startswith("invalid-"):
                expected = path.stem.removeprefix("invalid-")

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
