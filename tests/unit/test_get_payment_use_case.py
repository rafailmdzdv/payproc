# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from application.use_cases.get_payment import GetPaymentUseCase
from core.enums import Currency, PaymentStatus
from core.models import Payment
from tests.conftest import FakeUnitOfWork


async def test_get_payment_found(fake_uow: FakeUnitOfWork) -> None:
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        amount=Decimal('50.00'),
        currency=Currency.USD,
        description='Ride fare',
        metadata={},
        status=PaymentStatus.PENDING,
        idempotency_key='ride_123',
        webhook_url='https://taxi.com/hook',
        created_at=datetime.now(UTC),
    )
    await fake_uow.payments().add(payment)

    use_case = GetPaymentUseCase(fake_uow)
    dto = await use_case.execute(payment_id)

    assert dto is not None
    assert dto.id == payment_id
    assert dto.amount == Decimal('50.00')
    assert dto.currency == Currency.USD
    assert dto.status == PaymentStatus.PENDING


async def test_get_payment_not_found(fake_uow: FakeUnitOfWork) -> None:
    use_case = GetPaymentUseCase(fake_uow)
    dto = await use_case.execute(uuid.uuid4())
    assert dto is None
