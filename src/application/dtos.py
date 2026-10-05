# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, final

from core.enums import Currency, PaymentStatus


@final
@dataclass(slots=True, frozen=True)
class PaymentCreateDTO:
    """Input transfer object for initiating a payment."""

    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    webhook_url: str
    idempotency_key: str


@final
@dataclass(slots=True, frozen=True)
class PaymentDTO:
    """Output transfer object containing complete payment attributes."""

    id: uuid.UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None = None


@final
@dataclass(slots=True, frozen=True)
class PaymentCreatedEventDTO:
    """Event transfer object sent through outbox and broker."""

    payment_id: uuid.UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    webhook_url: str
    idempotency_key: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert event payload to dictionary format for JSON serialization."""
        return {
            'payment_id': str(self.payment_id),
            'amount': str(self.amount),
            'currency': self.currency.value,
            'description': self.description,
            'metadata': self.metadata,
            'webhook_url': self.webhook_url,
            'idempotency_key': self.idempotency_key,
            'created_at': self.created_at.isoformat(),
        }


@final
@dataclass(slots=True, frozen=True)
class WebhookNotificationDTO:
    """Webhook notification payload transfer object."""

    payment_id: uuid.UUID
    status: PaymentStatus
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    processed_at: datetime | None
    event: str = field(default='payment.processed')

    def to_dict(self) -> dict[str, Any]:
        """Serialize notification to dictionary format."""
        processed_iso = ''
        if self.processed_at is not None:
            processed_iso = self.processed_at.isoformat()

        return {
            'event': self.event,
            'payment_id': str(self.payment_id),
            'status': self.status.value,
            'amount': str(self.amount),
            'currency': self.currency.value,
            'description': self.description,
            'metadata': self.metadata,
            'processed_at': processed_iso,
        }
