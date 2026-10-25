"""Run one bounded paired conversation. Live inference requires explicit --live."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from game.agent_contracts import RuntimePolicy  # noqa: E402
from game.credentials import openrouter_key  # noqa: E402
from game.experiments import PairScenario, run_pair  # noqa: E402
from game.model_config import ModelConfig  # noqa: E402
from game.openrouter import CharacterRouter  # noqa: E402
from game.providers import ScriptedProvider  # noqa: E402


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, default=ROOT / "experiments/pair.json")
    parser.add_argument("--config", type=Path, help="Model configuration; omit for scripted control")
    parser.add_argument(
        "--key-file", type=Path, help="Server-side OpenRouter key file; never included in reports"
    )
    parser.add_argument("--live", action="store_true", help="Allow configured OpenRouter inference")
    parser.add_argument("--swap-models", action="store_true", help="Exchange models between the two personas")
    parser.add_argument(
        "--reverse-order", action="store_true", help="Reverse who hears the fixed opening first"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="New directory; includes private experiment dialogue"
    )
    args = parser.parse_args()
    scenario = PairScenario.model_validate_json(args.scenario.read_text())
    roster = json.loads((ROOT / "gameplay/characters.json").read_text())
    provider, policy, evidence = ScriptedProvider(), RuntimePolicy(), "scripted"
    if args.config:
        config = ModelConfig.model_validate_json(args.config.read_text())
        config.validate_roster(roster)
        hosted = any(p.kind == "openrouter" for p in config.profiles.values())
        if hosted and not args.live:
            parser.error("OpenRouter requests require --live; omit --config for the offline control")
        if args.swap_models:
            a, b = scenario.characters
            first = config.characters.get(a, config.default_profile)
            second = config.characters.get(b, config.default_profile)
            config.characters.update({a: second, b: first})
        provider = CharacterRouter(config, openrouter_key(args.key_file) if hosted else None)
        policy, evidence = config.policy, "live-openrouter" if hosted else "scripted"
    elif args.live or args.swap_models:
        parser.error("--live and --swap-models require --config")
    if args.reverse_order:
        scenario.first_seat = "player_blue" if scenario.first_seat == "player_red" else "player_red"
    # Validate all inputs before touching output, never overwrite previous evidence.
    args.output.mkdir(parents=True, exist_ok=False)
    report = await run_pair(
        args.output / "game.sqlite3", roster, scenario, provider, policy, evidence=evidence
    )
    (args.output / "report.json").write_text(report.model_dump_json(indent=2, by_alias=True) + "\n")
    attempts = [a for r in report.accounting.values() for a in r.attempts]
    print(
        json.dumps(
            {
                "status": report.status,
                "evidence": evidence,
                "turns": len(report.turns),
                "attempts": len(attempts),
                "charged_microusd": sum(a.charged_cost for a in attempts),
                "report": str(args.output / "report.json"),
            }
        )
    )
    return 0 if report.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
