"""Bounded asynchronous execution. Provider I/O never runs inside a database transaction."""

import asyncio
import json
from time import monotonic

from pydantic import ValidationError

from .agent_contracts import AgentRequest, ProviderResult, RuntimePolicy
from .core import GameError
from .providers import RetryableProviderError, ScriptedProvider


class AgentRuntime:
    def __init__(self, store, provider=None, policy=None, publish=lambda state: None):
        self.store = store
        self.provider = provider or ScriptedProvider()
        self.identity = self.provider.identity.model_copy(deep=True)
        self.policy = policy or RuntimePolicy()
        self.publish = publish
        self.tasks = {}
        self.provider_tasks = set()
        self.slots = asyncio.Semaphore(self.policy.concurrency)

    def schedule(self, state, actor):
        work = state["conversations"][actor]["work"]
        if not work or work["status"] != "pending" or work["request_id"] in self.tasks:
            return
        request_id = work["request_id"]
        job = self.store.job(request_id)
        if not job or job["status"] != "queued":
            return
        if len(self.tasks) >= self.policy.max_queued:
            self._finish(request_id, "failed", "capacity")
            return
        task = asyncio.create_task(self._run(request_id))
        self.tasks[request_id] = task
        task.add_done_callback(lambda done: self._completed(request_id, done))

    def _completed(self, request_id, task):
        self.tasks.pop(request_id, None)
        if task.cancelled():
            self._finish(request_id, "cancelled", "cancelled")
        elif task.exception() is not None:
            self._finish(request_id, "failed", "runtime_error")

    def _finish(self, request_id, status, error=None, result=None):
        state = self.store.finish_job(request_id, status, error, result)
        if state:
            self.publish(state)

    async def _run(self, request_id):
        job = self.store.job(request_id)
        policy = RuntimePolicy.model_validate_json(job["policy"])
        request = AgentRequest.model_validate_json(job["request"])
        if (
            json.loads(job["identity"]) != self.identity.model_dump()
            or self.provider.identity != self.identity
        ):
            self._finish(request_id, "failed", "provider_changed")
            return
        for _ in range(policy.max_attempts):
            attempt = None
            started = monotonic()
            provider_task = None
            try:

                async def invoke():
                    nonlocal attempt, started
                    async with self.slots:
                        attempt = self.store.reserve_attempt(request_id)
                        if attempt is None:
                            raise asyncio.CancelledError()
                        started = monotonic()
                        return await self.provider.generate(request.model_copy(deep=True))

                provider_task = asyncio.create_task(invoke())
                self.provider_tasks.add(provider_task)
                provider_task.add_done_callback(self._provider_completed)
                done, _ = await asyncio.wait({provider_task}, timeout=policy.timeout_seconds)
                if not done:
                    provider_task.cancel()
                    raise TimeoutError()
                raw = provider_task.result()
                result = ProviderResult.model_validate(raw)
                identity = self.identity
                usage = result.usage
                if (
                    usage.input_tokens > identity.max_input_tokens
                    or usage.output_tokens > identity.max_output_tokens
                    or usage.cost_microusd > identity.max_cost_microusd
                ):
                    self.store.record_attempt(
                        request_id, attempt, "usage_exceeded", self._latency(started), usage.model_dump()
                    )
                    self._finish(request_id, "failed", "usage_exceeded")
                    return
                self.store.record_attempt(
                    request_id, attempt, "succeeded", self._latency(started), usage.model_dump()
                )
                self._finish(request_id, "succeeded", result=result.model_dump())
                return
            except RetryableProviderError:
                if attempt:
                    self.store.record_attempt(request_id, attempt, "transient_error", self._latency(started))
                if attempt and attempt < policy.max_attempts:
                    continue
                self._finish(request_id, "failed", "provider_unavailable")
            except asyncio.CancelledError:
                if provider_task:
                    provider_task.cancel()
                if attempt:
                    self.store.record_attempt(request_id, attempt, "cancelled", self._latency(started))
                self._finish(request_id, "cancelled", "cancelled")
            except Exception as error:
                code = (
                    "timeout"
                    if isinstance(error, TimeoutError)
                    else "invalid_response"
                    if isinstance(error, ValidationError)
                    else error.code
                    if isinstance(error, GameError)
                    else "provider_error"
                )
                if attempt:
                    self.store.record_attempt(request_id, attempt, code, self._latency(started))
                self._finish(request_id, "failed", code)
            return

    @staticmethod
    def _latency(started):
        return max(0, round((monotonic() - started) * 1000))

    def _provider_completed(self, task):
        self.provider_tasks.discard(task)
        if not task.cancelled():
            task.exception()

    def cancel(self, request_id):
        task = self.tasks.get(request_id)
        if task:
            task.cancel()

    async def drain(self):
        if self.tasks:
            await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)

    async def close(self):
        for task in list(self.tasks.values()):
            task.cancel()
        await self.drain()
        for task in list(self.provider_tasks):
            task.cancel()
        if self.provider_tasks:
            # A noncooperative adapter cannot block shutdown or apply a late result.
            await asyncio.wait(self.provider_tasks, timeout=0.1)
