# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from typing import final

from application.dtos import PaymentDTO
from application.interfaces.uow import UnitOfWork
from core.models import Payment


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


@final
class GetPaymentUseCase:
    """Use case retrieving payment state by unique identifier."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize use case with Unit of Work dependency."""
        self._uow = uow

    async def execute(self, payment_id: uuid.UUID) -> PaymentDTO | None:
        """Fetch payment details by ID."""
        async with self._uow as transaction_uow:
            payment_entity = await transaction_uow.payments().get_by_id(
                payment_id,
            )
            if payment_entity is None:
                return None
            return _map_to_dto(payment_entity)
