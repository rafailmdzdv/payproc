# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from typing import final

from application.use_cases.relay_outbox import RelayOutboxUseCase
from infrastructure.config import settings

logger = logging.getLogger(__name__)


@final
class OutboxRelayWorker:
    """Continuous background worker orchestrating outbox relay use case."""

    def __init__(
        self,
        relay_use_case: RelayOutboxUseCase,
        poll_interval_sec: float = settings.outbox_poll_interval_sec,
        batch_size: int = settings.outbox_batch_size,
    ) -> None:
        """Initialize worker with relay use case and polling configurations."""
        self._relay_use_case = relay_use_case
        self._poll_interval = poll_interval_sec
        self._batch_size = batch_size
        self._running = False
        self._wake_event = asyncio.Event()

    def wake(self) -> None:
        """Signal worker to execute an immediate batch run."""
        self._wake_event.set()

    def stop(self) -> None:
        """Signal worker to terminate execution loop."""
        self._running = False
        self._wake_event.set()

    async def run(self) -> None:
        """Run continuous polling loop until stopped."""
        self._running = True
        logger.info('Outbox relay worker started')
        while self._running:
            try:
                await self._relay_use_case.execute(self._batch_size)
            except Exception:
                logger.exception('Outbox relay iteration failed')

            await self._wait_interval()

    async def _wait_interval(self) -> None:
        """Sleep until timeout or until explicitly signaled."""
        try:
            await asyncio.wait_for(
                self._wake_event.wait(),
                timeout=self._poll_interval,
            )
        except TimeoutError:
            return
        finally:
            self._wake_event.clear()
