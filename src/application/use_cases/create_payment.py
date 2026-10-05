# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import UTC, datetime
from typing import final

from application.dtos import (
    PaymentCreatedEventDTO,
    PaymentCreateDTO,
    PaymentDTO,
)
from application.interfaces.uow import UnitOfWork
from core.enums import OutboxStatus, PaymentStatus
from core.models import OutboxMessage, Payment

EVENT_PAYMENT_CREATED = 'payment.created'


def _map_to_dto(entity: Payment) -> PaymentDTO:
    """Map domain payment entity to application output DTO."""
    return PaymentDTO(
        id=entity.id,
        amount=entity.amount,
        currency=entity.currency,
        description=entity.description,
        metadata=entity.metadata,
        status=entity.status,
        idempotency_key=entity.idempotency_key,
        webhook_url=entity.webhook_url,
        created_at=entity.created_at,
        processed_at=entity.processed_at,
    )


def _build_outbox_message(
    payment: Payment,
    timestamp: datetime,
) -> OutboxMessage:
    """Build domain outbox message from payment entity."""
    event = PaymentCreatedEventDTO(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        webhook_url=payment.webhook_url,
        idempotency_key=payment.idempotency_key,
        created_at=timestamp,
    )
    return OutboxMessage(
        id=uuid.uuid4(),
        event_type=EVENT_PAYMENT_CREATED,
        payload=event.to_dict(),
        status=OutboxStatus.PENDING,
        created_at=timestamp,
    )


@final
class CreatePaymentUseCase:
    """Use case coordinating idempotent payment creation and outbox recording."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize use case with Unit of Work dependency."""
        self._uow = uow

    async def execute(
        self,
        payment_input: PaymentCreateDTO,
    ) -> tuple[PaymentDTO, bool]:
        """Execute transactional payment registration."""
        async with self._uow as transaction_uow:
            existing_payment = await transaction_uow.payments().get_by_idempotency_key(
                payment_input.idempotency_key,
            )
            if existing_payment is not None:
                return _map_to_dto(existing_payment), False

            now = datetime.now(UTC)
            payment = Payment(
                id=uuid.uuid4(),
                amount=payment_input.amount,
                currency=payment_input.currency,
                description=payment_input.description,
                metadata=payment_input.metadata,
                status=PaymentStatus.PENDING,
                idempotency_key=payment_input.idempotency_key,
                webhook_url=payment_input.webhook_url,
                created_at=now,
            )
            await transaction_uow.payments().add(payment)
            await transaction_uow.outbox().add(
                _build_outbox_message(payment, now),
            )
            await transaction_uow.commit()

            return _map_to_dto(payment), True
