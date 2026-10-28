"""Browser-test app; never used by the local/hosted game launchers."""

import asyncio
import os

from game.agent_contracts import RuntimePolicy
from game.app import create_app
from game.providers import ScriptedProvider


class BrowserTestProvider(ScriptedProvider):
    def __init__(self):
        super().__init__(delay_seconds=0.8)
        self.held = set()

    async def generate(self, request):
        key = (request.game_id, request.round_number, request.opponent)
        if (
            request.round_number == 1
            and request.messages[-1].content == "Let us build something together."
            and key not in self.held
        ):
            # Hold only the cancellation scenario's first attempt. A real cancel
            # interrupts this await; retry uses the normal scripted response.
            self.held.add(key)
            await asyncio.Event().wait()
        return await super().generate(request)


def create_e2e_app():
    if os.environ.get("GAME_TEST_MODE") == "model":
        return create_app()
    return create_app(provider=BrowserTestProvider(), policy=RuntimePolicy(timeout_seconds=120))
