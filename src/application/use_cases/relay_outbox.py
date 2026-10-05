# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import logging
from datetime import UTC, datetime
from typing import final

from application.interfaces.broker import MessagePublisher
from application.interfaces.uow import UnitOfWork
from core.models import OutboxMessage

logger = logging.getLogger(__name__)


@final
class RelayOutboxUseCase:
    """Use case retrieving unpublished outbox messages and pushing to message broker."""

    def __init__(
        self,
        uow: UnitOfWork,
        publisher: MessagePublisher,
        queue_name: str,
    ) -> None:
        """Initialize use case with required infrastructure ports."""
        self._uow = uow
        self._publisher = publisher
        self._queue_name = queue_name

    async def execute(self, batch_size: int) -> int:
        """Process batch of unpublished messages and dispatch them."""
        async with self._uow as transaction_uow:
            pending_messages = await transaction_uow.outbox.fetch_pending(
                batch_size,
            )
            if not pending_messages:
                return 0

            await self._dispatch_batch(transaction_uow, pending_messages)
            await transaction_uow.commit()
            return len(pending_messages)

    async def _dispatch_batch(
        self,
        uow: UnitOfWork,
        messages: list[OutboxMessage],
    ) -> None:
        """Iterate over outbox messages with while loop."""
        idx = 0
        total = len(messages)
        while idx < total:
            await self._dispatch_single(uow, messages[idx])
            idx += 1

    async def _dispatch_single(
        self,
        uow: UnitOfWork,
        message: OutboxMessage,
    ) -> None:
        """Publish single message and record status transition."""
        try:
            await self._publisher.publish(self._queue_name, message.payload)
        except Exception as pub_error:
            logger.warning(
                'Failed to publish outbox message %s: %s',
                str(message.id),
                str(pub_error),
            )
            await uow.outbox.increment_retry(message.id, str(pub_error))
        else:
            now = datetime.now(UTC)
            await uow.outbox.mark_published(message.id, now)
            logger.info(
                'Outbox message %s marked as published',
                str(message.id),
            )
