# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from application.use_cases.relay_outbox import RelayOutboxUseCase
from infrastructure.broker.rabbit import (
    RabbitMessagePublisher,
    broker,
    setup_broker,
)
from infrastructure.broker.relay_worker import OutboxRelayWorker
from infrastructure.config import settings
from infrastructure.database.session import async_session_factory, engine
from infrastructure.database.uow import SqlUnitOfWork
from server.api.v1.payments import router as payments_v1_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


async def _shutdown_resources(
    relay_worker: OutboxRelayWorker,
    relay_task: asyncio.Task[None],
) -> None:
    """Safely terminate background workers and close connection pools."""
    logger.info('Stopping outbox relay worker and releasing resources')
    relay_worker.stop()
    relay_task.cancel()
    await broker.stop()
    await engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001
    """Manage lifecycle resources for API application."""
    await broker.connect()
    await setup_broker(broker)

    publisher = RabbitMessagePublisher(broker)
    uow = SqlUnitOfWork(session_factory=async_session_factory)
    relay_use_case = RelayOutboxUseCase(
        uow=uow,
        publisher=publisher,
        queue_name=settings.queue_name,
    )
    relay_worker = OutboxRelayWorker(relay_use_case=relay_use_case)
    relay_task = asyncio.create_task(relay_worker.run())

    try:
        yield
    finally:
        await _shutdown_resources(relay_worker, relay_task)


app = FastAPI(
    title='Payment Processing Service',
    description='Asynchronous payment processing service with Onion Architecture',
    version='1.0.0',
    lifespan=lifespan,
)

app.include_router(payments_v1_router, prefix='/api/v1')


@app.get('/health', tags=['system'], summary='Service health status')
async def health_check() -> dict[str, str]:
    """Check service availability."""
    return {'status': 'ok'}
