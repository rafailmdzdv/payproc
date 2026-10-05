# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import asyncio
import datetime as dt
import logging
import uuid
from typing import Any

from faststream import FastStream

from application.use_cases.process_payment import ProcessPaymentUseCase
from infrastructure.broker import rabbit as rabbit_broker
from infrastructure.config import settings
from infrastructure.database import (
    session as db_session,
)
from infrastructure.database import (
    uow as db_uow,
)
from infrastructure.gateway.emulator import GatewayEmulator
from infrastructure.webhook.sender import HttpWebhookSender

logger = logging.getLogger(__name__)

INITIAL_ATTEMPT = 1

app = FastStream(rabbit_broker.broker)
gateway_emulator = GatewayEmulator()
webhook_sender = HttpWebhookSender()


@app.after_startup
async def after_startup() -> None:
    """Initialize queues and exchanges on RabbitMQ broker."""
    await rabbit_broker.setup_broker(rabbit_broker.broker)
    logger.info('Broker topology declared and consumer ready')


def _get_process_use_case() -> ProcessPaymentUseCase:
    """Create ProcessPaymentUseCase instance with configured adapters."""
    uow = db_uow.SqlUnitOfWork(session_factory=db_session.async_session_factory)
    return ProcessPaymentUseCase(
        uow=uow,
        gateway=gateway_emulator,
        webhook_sender=webhook_sender,
    )


async def _route_to_dlq(payload: dict[str, Any], failure_reason: str) -> None:
    """Forward exhausted message to Dead Letter Queue."""
    dlq_message = {
        'original_payload': payload,
        'error': failure_reason,
        'failed_at': dt.datetime.now(dt.UTC).isoformat(),
        'total_attempts': settings.consumer_max_retries,
    }
    await rabbit_broker.broker.publish(dlq_message, queue=settings.dlq_name)
    logger.error('Routed failed message to DLQ: %s', failure_reason)


@rabbit_broker.broker.subscriber(rabbit_broker.main_queue)
async def handle_payment_event(payload: dict[str, Any]) -> None:
    """Consume payment creation events with retries and dead letter routing."""
    payment_raw_id = payload.get('payment_id')
    if not payment_raw_id:
        logger.error('Missing payment_id in queue message: %s', payload)
        return

    payment_id = uuid.UUID(str(payment_raw_id))
    attempt = INITIAL_ATTEMPT
    last_error_message = ''
    use_case = _get_process_use_case()

    while attempt <= settings.consumer_max_retries:
        try:
            await use_case.execute(payment_id)
        except Exception as process_error:
            last_error_message = str(process_error)
            logger.warning(
                'Payment %s processing failed on attempt %d/%d: %s',
                str(payment_id),
                attempt,
                settings.consumer_max_retries,
                last_error_message,
            )
        else:
            return

        if attempt < settings.consumer_max_retries:
            await asyncio.sleep(
                settings.consumer_backoff_factor ** (attempt - 1),
            )
        attempt += 1

    await _route_to_dlq(payload, last_error_message)


@rabbit_broker.broker.subscriber(rabbit_broker.dlq_queue)
async def handle_dlq_message(dlq_payload: dict[str, Any]) -> None:
    """Log messages received in Dead Letter Queue for audit and alerting."""
    logger.warning('Dead Letter Queue received message: %s', dlq_payload)
