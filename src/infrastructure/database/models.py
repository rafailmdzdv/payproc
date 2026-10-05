# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Final, final

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.enums import OutboxStatus, PaymentStatus

MAX_CURRENCY_LEN: Final = 3
MAX_STATUS_LEN: Final = 20
MAX_DESCRIPTION_LEN: Final = 255
MAX_IDEMPOTENCY_KEY_LEN: Final = 255
MAX_URL_LEN: Final = 2048
MAX_EVENT_TYPE_LEN: Final = 100
AMOUNT_PRECISION: Final = 12
AMOUNT_SCALE: Final = 2


class Base(DeclarativeBase):  # noqa: FIN100
    """Declarative base."""


@final
class PaymentTable(Base):
    """Database table mapping for payment records."""

    __tablename__ = 'payments'

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=AMOUNT_PRECISION, scale=AMOUNT_SCALE),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(length=MAX_CURRENCY_LEN),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(length=MAX_DESCRIPTION_LEN),
        nullable=False,
    )
    payment_metadata: Mapped[dict[str, Any]] = mapped_column(
        'metadata',
        JSON,
        nullable=False,
        default=dict,
    )
    status: Mapped[str] = mapped_column(
        String(length=MAX_STATUS_LEN),
        nullable=False,
        default=PaymentStatus.PENDING.value,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(length=MAX_IDEMPOTENCY_KEY_LEN),
        unique=True,
        index=True,
        nullable=False,
    )
    webhook_url: Mapped[str] = mapped_column(
        String(length=MAX_URL_LEN),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


@final
class OutboxTable(Base):
    """Database table mapping for outbox messages."""

    __tablename__ = 'outbox'

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[str] = mapped_column(
        String(length=MAX_EVENT_TYPE_LEN),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(length=MAX_STATUS_LEN),
        nullable=False,
        default=OutboxStatus.PENDING.value,
        index=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
