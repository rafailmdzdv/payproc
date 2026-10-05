# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import UTC, datetime
from typing import final

from application.dtos import WebhookNotificationDTO
from application.interfaces.gateway import PaymentGateway
from application.interfaces.uow import UnitOfWork
from application.interfaces.webhook import WebhookSender
from core.enums import PaymentStatus
from core.exceptions import PaymentNotFoundError
from core.models import Payment


def _build_notification(
    payment: Payment,
    status: PaymentStatus,
    timestamp: datetime,
) -> WebhookNotificationDTO:
    """Build webhook notification DTO from payment entity."""
    return WebhookNotificationDTO(
        payment_id=payment.id,
        status=status,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        processed_at=timestamp,
    )


@final
class ProcessPaymentUseCase:
    """Use case coordinating gateway emulation, status updates, and webhook dispatch."""

    def __init__(
        self,
        uow: UnitOfWork,
        gateway: PaymentGateway,
        webhook_sender: WebhookSender,
    ) -> None:
        """Initialize use case with required ports."""
        self._uow = uow
        self._gateway = gateway
        self._webhook = webhook_sender

    async def execute(self, payment_id: uuid.UUID) -> None:
        """Execute payment gateway processing and webhook notification."""
        async with self._uow as transaction_uow:
            payment = await transaction_uow.payments.get_by_id(payment_id)
            if payment is None:
                raise PaymentNotFoundError(payment_id)

            if payment.status != PaymentStatus.PENDING:
                await self._notify_terminal(payment)
                return

            outcome, processed_at = await self._process_gateway_turn(
                transaction_uow,
                payment,
            )

        notification = _build_notification(payment, outcome, processed_at)
        await self._webhook.send(payment.webhook_url, notification.to_dict())

    async def _notify_terminal(self, payment: Payment) -> None:
        """Notify client of already processed payment."""
        timestamp = payment.processed_at or datetime.now(UTC)
        notification = _build_notification(payment, payment.status, timestamp)
        await self._webhook.send(payment.webhook_url, notification.to_dict())

    async def _process_gateway_turn(
        self,
        uow: UnitOfWork,
        payment: Payment,
    ) -> tuple[PaymentStatus, datetime]:
        """Execute external gateway call and commit updated status."""
        outcome = await self._gateway.execute(
            payment.id,
            payment.amount,
            payment.currency,
        )
        now = datetime.now(UTC)
        await uow.payments.update_status(payment.id, outcome, now)
        await uow.commit()
        return outcome, now
