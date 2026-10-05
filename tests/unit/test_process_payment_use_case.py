# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from application.use_cases.process_payment import ProcessPaymentUseCase
from core.enums import Currency, PaymentStatus
from core.exceptions import PaymentNotFoundError
from core.models import Payment
from tests.conftest import FakeGateway, FakeUnitOfWork, FakeWebhookSender


async def test_process_pending_payment_success(
    fake_uow: FakeUnitOfWork,
    fake_gateway: FakeGateway,
    fake_webhook: FakeWebhookSender,
) -> None:
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        amount=Decimal('300.00'),
        currency=Currency.EUR,
        description='Invoice payment',
        metadata={'invoice_id': 'inv_01'},
        status=PaymentStatus.PENDING,
        idempotency_key='idemp_inv_01',
        webhook_url='https://client.site/hook',
        created_at=datetime.now(UTC),
    )
    await fake_uow.payments.add(payment)

    use_case = ProcessPaymentUseCase(
        uow=fake_uow,
        gateway=fake_gateway,
        webhook_sender=fake_webhook,
    )
    await use_case.execute(payment_id)

    assert len(fake_gateway.calls) == 1
    assert fake_gateway.calls[0] == (payment_id, Decimal('300.00'), Currency.EUR)

    updated_payment = await fake_uow.payments.get_by_id(payment_id)
    assert updated_payment is not None
    assert updated_payment.status == PaymentStatus.SUCCEEDED
    assert updated_payment.processed_at is not None
    assert fake_uow.committed is True

    assert len(fake_webhook.dispatched) == 1
    url, payload = fake_webhook.dispatched[0]
    assert url == 'https://client.site/hook'
    assert payload['payment_id'] == str(payment_id)
    assert payload['status'] == 'succeeded'


async def test_process_payment_not_found(
    fake_uow: FakeUnitOfWork,
    fake_gateway: FakeGateway,
    fake_webhook: FakeWebhookSender,
) -> None:
    use_case = ProcessPaymentUseCase(
        uow=fake_uow,
        gateway=fake_gateway,
        webhook_sender=fake_webhook,
    )
    missing_id = uuid.uuid4()
    with pytest.raises(PaymentNotFoundError):
        await use_case.execute(missing_id)

    assert len(fake_gateway.calls) == 0
    assert len(fake_webhook.dispatched) == 0


async def test_process_already_processed_payment(
    fake_uow: FakeUnitOfWork,
    fake_gateway: FakeGateway,
    fake_webhook: FakeWebhookSender,
) -> None:
    payment_id = uuid.uuid4()
    now = datetime.now(UTC)
    payment = Payment(
        id=payment_id,
        amount=Decimal('120.00'),
        currency=Currency.RUB,
        description='Coffee order',
        metadata={},
        status=PaymentStatus.SUCCEEDED,
        idempotency_key='idemp_coffee_01',
        webhook_url='https://client.site/hook',
        created_at=now,
        processed_at=now,
    )
    await fake_uow.payments.add(payment)

    use_case = ProcessPaymentUseCase(
        uow=fake_uow,
        gateway=fake_gateway,
        webhook_sender=fake_webhook,
    )
    await use_case.execute(payment_id)
    _, payload = fake_webhook.dispatched[0]

    assert len(fake_gateway.calls) == 0
    assert len(fake_webhook.dispatched) == 1
    assert payload['status'] == 'succeeded'
