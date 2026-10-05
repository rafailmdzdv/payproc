# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import asyncio

from application.use_cases.relay_outbox import RelayOutboxUseCase
from infrastructure.broker.relay_worker import OutboxRelayWorker
from tests.conftest import FakePublisher, FakeUnitOfWork


async def test_relay_worker_lifecycle(
    fake_uow: FakeUnitOfWork,
    fake_publisher: FakePublisher,
) -> None:
    use_case = RelayOutboxUseCase(
        uow=fake_uow,
        publisher=fake_publisher,
        queue_name='test_queue',
    )
    worker = OutboxRelayWorker(
        relay_use_case=use_case,
        poll_interval_sec=0.01,
        batch_size=10,
    )

    worker_task = asyncio.create_task(worker.run())
    worker.wake()
    await asyncio.sleep(0.02)
    worker.stop()
    await worker_task

    assert worker_task.done()


async def test_relay_worker_handles_exception() -> None:
    from unittest.mock import AsyncMock

    failing_use_case = AsyncMock()
    failing_use_case.execute.side_effect = RuntimeError('Database timeout')

    worker = OutboxRelayWorker(
        relay_use_case=failing_use_case,
        poll_interval_sec=0.01,
        batch_size=5,
    )
    worker_task = asyncio.create_task(worker.run())
    await asyncio.sleep(0.02)
    worker.stop()
    await worker_task

    assert worker_task.done()
    assert failing_use_case.execute.call_count >= 1
