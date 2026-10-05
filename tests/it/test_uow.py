# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from core.enums import Currency, PaymentStatus
from core.models import Payment
from infrastructure.database.uow import SqlUnitOfWork


async def test_uow_commit_persists(it_uow: SqlUnitOfWork) -> None:
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        amount=Decimal('50.00'),
        currency=Currency.USD,
        description='UOW commit test',
        metadata={},
        status=PaymentStatus.PENDING,
        idempotency_key='uow_key_01',
        webhook_url='https://site.org/hook',
        created_at=datetime.now(UTC),
    )

    async with it_uow as uow:
        await uow.payments.add(payment)
        await uow.commit()

    async with it_uow as uow:
        retrieved = await uow.payments.get_by_id(payment_id)
        assert retrieved is not None
        assert retrieved.id == payment_id


async def test_uow_rollback_on_error(it_uow: SqlUnitOfWork) -> None:
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        amount=Decimal('75.00'),
        currency=Currency.EUR,
        description='UOW rollback test',
        metadata={},
        status=PaymentStatus.PENDING,
        idempotency_key='uow_key_02',
        webhook_url='https://site.org/hook',
        created_at=datetime.now(UTC),
    )

    with pytest.raises(RuntimeError):  # noqa: PT012
        async with it_uow as uow:
            await uow.payments.add(payment)
            raise RuntimeError('Intentional error triggering rollback')

    async with it_uow as uow:
        retrieved = await uow.payments.get_by_id(payment_id)
        assert retrieved is None


async def test_uow_unentered_commit_noop(it_uow: SqlUnitOfWork) -> None:
    await it_uow.commit()


async def test_uow_unentered_rollback_noop(it_uow: SqlUnitOfWork) -> None:
    await it_uow.rollback()
