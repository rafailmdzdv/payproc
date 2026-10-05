# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import datetime
from typing import final, override

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from application.interfaces.repositories import (
    OutboxRepository,
    PaymentRepository,
)
from core.enums import Currency, OutboxStatus, PaymentStatus
from core.models import OutboxMessage, Payment
from infrastructure.database.models import OutboxTable, PaymentTable


def _to_payment_entity(table_row: PaymentTable) -> Payment:
    """Convert SQLAlchemy row to domain payment entity."""
    return Payment(
        id=table_row.id,
        amount=table_row.amount,
        currency=Currency(table_row.currency),
        description=table_row.description,
        metadata=table_row.payment_metadata,
        status=PaymentStatus(table_row.status),
        idempotency_key=table_row.idempotency_key,
        webhook_url=table_row.webhook_url,
        created_at=table_row.created_at,
        processed_at=table_row.processed_at,
    )


def _to_outbox_entity(table_row: OutboxTable) -> OutboxMessage:
    """Convert SQLAlchemy row to domain outbox entity."""
    return OutboxMessage(
        id=table_row.id,
        event_type=table_row.event_type,
        payload=table_row.payload,
        status=OutboxStatus(table_row.status),
        retry_count=table_row.retry_count,
        error_message=table_row.error_message,
        created_at=table_row.created_at,
        published_at=table_row.published_at,
    )


@final
class SqlPaymentRepository(PaymentRepository):
    """SQLAlchemy implementation of PaymentRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session."""
        self._session = session

    @override
    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        """Query payment by primary key UUID."""
        stmt = select(PaymentTable).where(PaymentTable.id == payment_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return _to_payment_entity(row)

    @override
    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Payment | None:
        """Query payment by unique idempotency key."""
        stmt = select(PaymentTable).where(
            PaymentTable.idempotency_key == idempotency_key,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return _to_payment_entity(row)

    @override
    async def add(self, payment: Payment) -> None:
        """Persist new payment entity to database table."""
        record = PaymentTable(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency.value,
            description=payment.description,
            payment_metadata=payment.metadata,
            status=payment.status.value,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
        self._session.add(record)

    @override
    async def update_status(
        self,
        payment_id: uuid.UUID,
        status: PaymentStatus,
        processed_at: datetime,
    ) -> Payment:
        """Update payment status and processed timestamp."""
        stmt = (
            update(PaymentTable)
            .where(PaymentTable.id == payment_id)
            .values(status=status.value, processed_at=processed_at)
            .returning(PaymentTable)
        )
        row = (await self._session.execute(stmt)).scalar_one()
        return _to_payment_entity(row)


@final
class SqlOutboxRepository(OutboxRepository):
    """SQLAlchemy implementation of OutboxRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session."""
        self._session = session

    @override
    async def add(self, message: OutboxMessage) -> None:
        """Insert new outbox message record."""
        record = OutboxTable(
            id=message.id,
            event_type=message.event_type,
            payload=message.payload,
            status=message.status.value,
            retry_count=message.retry_count,
            error_message=message.error_message,
            created_at=message.created_at,
            published_at=message.published_at,
        )
        self._session.add(record)

    @override
    async def fetch_pending(self, limit: int) -> list[OutboxMessage]:
        """Query unpublished outbox messages with row locking."""
        stmt = (
            select(OutboxTable)
            .where(OutboxTable.status == OutboxStatus.PENDING.value)
            .order_by(OutboxTable.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        records = (await self._session.execute(stmt)).scalars().all()
        return [_to_outbox_entity(row) for row in records]

    @override
    async def mark_published(
        self,
        message_id: uuid.UUID,
        published_at: datetime,
    ) -> None:
        """Transition outbox record to published status."""
        stmt = (
            update(OutboxTable)
            .where(OutboxTable.id == message_id)
            .values(
                status=OutboxStatus.PUBLISHED.value,
                published_at=published_at,
            )
        )
        await self._session.execute(stmt)

    @override
    async def increment_retry(
        self,
        message_id: uuid.UUID,
        error_message: str,
    ) -> None:
        """Increment retry counter and record failure diagnostics."""
        stmt = (
            update(OutboxTable)
            .where(OutboxTable.id == message_id)
            .values(
                retry_count=OutboxTable.retry_count + 1,
                error_message=error_message,
            )
        )
        await self._session.execute(stmt)
