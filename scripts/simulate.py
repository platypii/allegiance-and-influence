"""Run the scripted baseline headlessly through the same command/store boundary."""

import argparse
import json
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from game.models import CreateGame  # noqa: E402
from game.store import Store  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=32)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--agents", type=int, default=6)
    parser.add_argument("--output", type=Path, help="Optional replay JSON file")
    args = parser.parse_args()
    config = CreateGame(seed=args.seed, num_rounds=args.rounds, num_agents=args.agents)
    with tempfile.TemporaryDirectory() as temporary:
        store = Store(
            Path(temporary) / "game.db", json.loads((ROOT / "gameplay/characters.json").read_text())
        )
        game = store.create(config.model_dump())
        tokens = {seat: uuid.uuid4().hex for seat in ["player_red", "player_blue"]}
        for seat, token in tokens.items():
            game = store.join(game["id"], seat, token)

        def send(token, kind, **fields):
            nonlocal game
            game, _ = store.apply(
                game["id"],
                token,
                {
                    "kind": kind,
                    "command_id": uuid.uuid4().hex,
                    "expected_version": game["version"],
                    **fields,
                },
            )

        while game["phase"] != "finished":
            for i, token in enumerate(tokens.values()):
                send(token, "select", target=game["agents"][i]["UID"])
            for token in tokens.values():
                for text in ["Let us work together.", "We share a purpose."]:
                    send(token, "message", text=text)
                send(token, "done")
            if game["phase"] == "round_complete":
                send(next(iter(tokens.values())), "advance")
        result = {
            "mode": game["mode"],
            "rules_version": game["rules_version"],
            "config": game["config"],
            "winner": game["winner"],
            "scores": game["scores"],
            "model_calls": 0,
        }
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps({"manifest": result, "frames": store.replay(game["id"], None)}, indent=2) + "\n"
            )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
