# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.enums import Currency, OutboxStatus, PaymentStatus
from core.models import OutboxMessage, Payment
from infrastructure.database.repositories import (
    SqlOutboxRepository,
    SqlPaymentRepository,
)


def _build_test_payment(payment_id: uuid.UUID, key: str) -> Payment:
    return Payment(
        id=payment_id,
        amount=Decimal('199.99'),
        currency=Currency.RUB,
        description='Premium subscription',
        metadata={'plan': 'pro'},
        status=PaymentStatus.PENDING,
        idempotency_key=key,
        webhook_url='https://domain.tld/hook',
        created_at=datetime.now(UTC),
    )


async def test_payment_repo_add_and_get_by_id(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    payment_id = uuid.uuid4()
    payment = _build_test_payment(payment_id, 'idemp_by_id')

    async with db_session_factory() as session:
        repo = SqlPaymentRepository(session)
        await repo.add(payment)
        await session.commit()

    async with db_session_factory() as session:
        repo = SqlPaymentRepository(session)
        loaded = await repo.get_by_id(payment_id)
        assert loaded is not None
        assert loaded.id == payment_id
        assert loaded.amount == Decimal('199.99')


async def test_payment_repo_get_by_idempotency_key(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    payment_id = uuid.uuid4()
    payment = _build_test_payment(payment_id, 'idemp_by_key')

    async with db_session_factory() as session:
        repo = SqlPaymentRepository(session)
        await repo.add(payment)
        await session.commit()

    async with db_session_factory() as session:
        repo = SqlPaymentRepository(session)
        by_key = await repo.get_by_idempotency_key('idemp_by_key')
        assert by_key is not None
        assert by_key.id == payment_id


async def test_payment_repo_get_missing_returns_none(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with db_session_factory() as session:
        repo = SqlPaymentRepository(session)
        missing = await repo.get_by_id(uuid.uuid4())
        assert missing is None


async def test_payment_repo_update_status(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    payment_id = uuid.uuid4()
    payment = _build_test_payment(payment_id, 'idemp_status')

    async with db_session_factory() as session:
        repo = SqlPaymentRepository(session)
        await repo.add(payment)
        await session.commit()

    async with db_session_factory() as session:
        repo = SqlPaymentRepository(session)
        now = datetime.now(UTC)
        updated = await repo.update_status(payment_id, PaymentStatus.SUCCEEDED, now)
        await session.commit()
        assert updated.status == PaymentStatus.SUCCEEDED


async def test_outbox_repo_add_and_fetch_pending(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    message_id = uuid.uuid4()
    message = OutboxMessage(
        id=message_id,
        event_type='payment.created',
        payload={'order': 1},
        status=OutboxStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    async with db_session_factory() as session:
        repo = SqlOutboxRepository(session)
        await repo.add(message)
        await session.commit()

    async with db_session_factory() as session:
        repo = SqlOutboxRepository(session)
        pending = await repo.fetch_pending(10)
        assert len(pending) == 1
        assert pending[0].id == message_id


async def test_outbox_repo_increment_retry(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    message_id = uuid.uuid4()
    message = OutboxMessage(
        id=message_id,
        event_type='payment.created',
        payload={'order': 2},
        status=OutboxStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    async with db_session_factory() as session:
        repo = SqlOutboxRepository(session)
        await repo.add(message)
        await session.commit()

    async with db_session_factory() as session:
        repo = SqlOutboxRepository(session)
        await repo.increment_retry(message_id, 'Broker timeout')
        await session.commit()

    async with db_session_factory() as session:
        repo = SqlOutboxRepository(session)
        pending = await repo.fetch_pending(10)
        assert len(pending) == 1
        assert pending[0].retry_count == 1
        assert pending[0].error_message == 'Broker timeout'


async def test_outbox_repo_mark_published(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    message_id = uuid.uuid4()
    message = OutboxMessage(
        id=message_id,
        event_type='payment.created',
        payload={'order': 3},
        status=OutboxStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    async with db_session_factory() as session:
        repo = SqlOutboxRepository(session)
        await repo.add(message)
        await session.commit()

    async with db_session_factory() as session:
        repo = SqlOutboxRepository(session)
        await repo.mark_published(message_id, datetime.now(UTC))
        await session.commit()

        pending_empty = await repo.fetch_pending(10)
        assert len(pending_empty) == 0
