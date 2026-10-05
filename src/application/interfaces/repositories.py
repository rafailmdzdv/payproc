# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import datetime
from typing import Protocol

from core.enums import PaymentStatus
from core.models import OutboxMessage, Payment


class PaymentRepository(Protocol):
    """Payment persistence operations contract."""

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        """Fetch payment by unique identifier."""

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Payment | None:
        """Fetch payment by idempotency key."""

    async def add(self, payment: Payment) -> None:
        """Add new payment to repository."""

    async def update_status(
        self,
        payment_id: uuid.UUID,
        status: PaymentStatus,
        processed_at: datetime,
    ) -> Payment:
        """Update payment status and processed timestamp."""


class OutboxRepository(Protocol):
    """Outbox persistence operations contract."""

    async def add(self, message: OutboxMessage) -> None:
        """Add new outbox record."""

    async def fetch_pending(self, limit: int) -> list[OutboxMessage]:
        """Fetch batch of pending outbox messages."""

    async def mark_published(
        self,
        message_id: uuid.UUID,
        published_at: datetime,
    ) -> None:
        """Mark outbox message as published."""

    async def increment_retry(
        self,
        message_id: uuid.UUID,
        error_message: str,
    ) -> None:
        """Record failed publish attempt."""
