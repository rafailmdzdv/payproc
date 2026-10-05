# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, final

from core.enums import Currency, OutboxStatus, PaymentStatus


@final
@dataclass(slots=True)
class Payment:
    """Payment domain entity representing a processed customer payment."""

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
@dataclass(slots=True)
class OutboxMessage:
    """Outbox domain entity representing an asynchronous event to publish."""

    id: uuid.UUID
    event_type: str
    payload: dict[str, Any]
    status: OutboxStatus
    retry_count: int = 0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    published_at: datetime | None = None
