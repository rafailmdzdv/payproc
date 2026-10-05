# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from decimal import Decimal

from application.dtos import PaymentCreateDTO
from application.use_cases.create_payment import CreatePaymentUseCase
from core.enums import Currency, PaymentStatus
from tests.conftest import FakeUnitOfWork


async def test_create_new_payment_success(fake_uow: FakeUnitOfWork) -> None:
    use_case = CreatePaymentUseCase(fake_uow)
    dto = PaymentCreateDTO(
        amount=Decimal('150.00'),
        currency=Currency.RUB,
        description='Top-up wallet',
        metadata={'user_id': 'usr_99'},
        webhook_url='https://client.site/webhook',
        idempotency_key='idemp_unique_001',
    )

    payment_dto, is_created = await use_case.execute(dto)

    assert is_created is True
    assert payment_dto.amount == Decimal('150.00')
    assert payment_dto.currency == Currency.RUB
    assert payment_dto.status == PaymentStatus.PENDING
    assert fake_uow.committed is True

    saved_payment = await fake_uow.payments.get_by_id(payment_dto.id)
    assert saved_payment is not None
    assert saved_payment.idempotency_key == 'idemp_unique_001'

    pending_messages = await fake_uow.outbox.fetch_pending(10)
    assert len(pending_messages) == 1
    assert pending_messages[0].event_type == 'payment.created'
    assert pending_messages[0].payload['payment_id'] == str(payment_dto.id)


async def test_create_payment_idempotent_existing(fake_uow: FakeUnitOfWork) -> None:
    use_case = CreatePaymentUseCase(fake_uow)
    dto = PaymentCreateDTO(
        amount=Decimal('200.00'),
        currency=Currency.USD,
        description='First attempt',
        metadata={},
        webhook_url='https://client.site/webhook',
        idempotency_key='same_key_123',
    )

    first_payment, first_created = await use_case.execute(dto)
    assert first_created is True

    second_payment, second_created = await use_case.execute(dto)
    assert second_created is False
    assert second_payment.id == first_payment.id
    assert second_payment.status == PaymentStatus.PENDING

    pending_messages = await fake_uow.outbox.fetch_pending(10)
    assert len(pending_messages) == 1
