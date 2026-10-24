"""Prepare model settings and a private key file; inspect choices without running inference."""

import argparse
import getpass
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from game.model_config import ModelConfig  # noqa: E402

CATALOG_URL = "https://openrouter.ai/api/v1/models"


def save_key(path, value):
    value = value.strip()
    if not value or len(value) > 4096 or any(c.isspace() for c in value):
        raise ValueError("Enter a single nonempty API key")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents overwriting a key or following an existing symlink.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        output.write(value + "\n")


def inspect_config(path):
    config = ModelConfig.model_validate_json(path.read_text())
    roster = json.loads((ROOT / "gameplay/characters.json").read_text())
    config.validate_roster(roster)
    profiles = {}
    for name, profile in config.profiles.items():
        reserve = profile.cost_ceiling() if profile.kind == "openrouter" else 0
        profiles[name] = {
            "kind": profile.kind,
            "model": profile.model,
            "output_format": profile.output_format,
            "reservation_usd": str(Decimal(reserve) / 1000000),
            "fits_game_budget": reserve <= config.policy.cost_limit_microusd,
            "max_input_tokens": profile.max_input_tokens,
            "max_output_tokens": profile.max_output_tokens,
        }
    return {
        "default_profile": config.default_profile,
        "characters": config.characters,
        "game_budget_usd": str(Decimal(config.policy.cost_limit_microusd) / 1000000),
        "call_limit": config.policy.call_limit,
        "profiles": profiles,
        "note": "Local validation only: does not check credentials, model availability, or current prices.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Copy the editable model setup template; never overwrite")
    init.add_argument("--config", type=Path, default=ROOT / "data/models.json")
    key = commands.add_parser("key", help="Prompt privately and create an owner-only key file")
    key.add_argument("--file", type=Path, default=ROOT / "data/openrouter.key")
    check = commands.add_parser("check", help="Show assignments and budget reservations without inference")
    check.add_argument("--config", type=Path, default=ROOT / "data/models.json")
    catalog = commands.add_parser("catalog", help="Read the public OpenRouter catalog; no key/inference")
    catalog.add_argument("--search", default="", help="Match model ID or display name")
    catalog.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    try:
        if args.command == "init":
            args.config.parent.mkdir(parents=True, exist_ok=True)
            with args.config.open("x") as output:
                output.write((ROOT / "config/models.example.json").read_text())
            print(
                f"Created {args.config}. Edit model IDs, profile names, assignments, and price/budget limits."
            )
        elif args.command == "key":
            if not sys.stdin.isatty():
                parser.error("Run the key command in an interactive terminal; input is not echoed")
            save_key(args.file, getpass.getpass("OpenRouter key (hidden): "))
            print(f"Saved key to {args.file} with owner-only permissions. The key was not displayed.")
        elif args.command == "check":
            print(json.dumps(inspect_config(args.config), indent=2))
        else:
            if not 1 <= args.limit <= 100:
                parser.error("--limit must be between 1 and 100")
            with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
                response = client.get(CATALOG_URL)
                response.raise_for_status()
                models = response.json()["data"]
            matches = [
                m
                for m in models
                if args.search.lower() in (m["id"] + " " + m["name"]).lower()
                and "text" in m.get("architecture", {}).get("output_modalities", [])
            ]
            print(
                json.dumps(
                    {
                        "source": CATALOG_URL,
                        "matching_models": len(matches),
                        "shown": min(len(matches), args.limit),
                        "models": [
                            {
                                "id": m["id"],
                                "name": m["name"],
                                "context_length": m["context_length"],
                                "prompt_usd_per_million": str(Decimal(m["pricing"]["prompt"]) * 1000000),
                                "completion_usd_per_million": str(
                                    Decimal(m["pricing"]["completion"]) * 1000000
                                ),
                                "supported_parameters": m.get("supported_parameters", []),
                            }
                            for m in matches[: args.limit]
                        ],
                        "note": "Catalog listing, not a quality ranking or guarantee of an available route.",
                    },
                    indent=2,
                )
            )
    except FileExistsError:
        parser.exit(2, "File already exists; existing settings/key were left untouched.\n")
    except (ValueError, OSError, httpx.HTTPError):
        # Do not print input values, key content, or a response body on failure.
        parser.exit(2, "Setup failed. Check file access, configuration values, or catalog connectivity.\n")


if __name__ == "__main__":
    main()
