# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, final

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from core.enums import Currency

MAX_DESCRIPTION_LEN = 255
DECIMAL_PLACES_COUNT = 2


@final
class PaymentCreateRequest(BaseModel):
    """Request payload for initiating payment processing."""

    model_config = ConfigDict(extra='forbid')

    amount: Decimal = Field(
        gt=0,
        decimal_places=DECIMAL_PLACES_COUNT,
        description='Payment transaction amount',
    )
    currency: Currency = Field(
        description='Payment currency (RUB, USD, EUR)',
    )
    description: str = Field(
        min_length=1,
        max_length=MAX_DESCRIPTION_LEN,
        description='Payment description text',
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description='Arbitrary additional key-value metadata',
    )
    webhook_url: HttpUrl = Field(
        description='Client webhook endpoint URL for asynchronous callback',
    )


@final
class PaymentCreateResponse(BaseModel):
    """Response returned upon acceptance of payment request."""

    model_config = ConfigDict(from_attributes=True)

    payment_id: uuid.UUID = Field(
        description='Unique identifier assigned to created payment',
    )
    status: str = Field(
        description='Current payment state (pending)',
    )
    created_at: datetime = Field(
        description='Payment creation timestamp',
    )


@final
class PaymentDetailResponse(BaseModel):
    """Detailed view model of payment state."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        description='Unique payment identifier',
    )
    amount: Decimal = Field(
        description='Payment amount',
    )
    currency: str = Field(
        description='Currency code',
    )
    description: str = Field(
        description='Payment description',
    )
    metadata: dict[str, Any] = Field(
        description='Payment metadata dictionary',
    )
    status: str = Field(
        description='Payment current status',
    )
    idempotency_key: str = Field(
        description='Idempotency key associated with payment',
    )
    webhook_url: str = Field(
        description='Webhook callback URL',
    )
    created_at: datetime = Field(
        description='Creation timestamp',
    )
    processed_at: datetime | None = Field(
        default=None,
        description='Processing completion timestamp',
    )
