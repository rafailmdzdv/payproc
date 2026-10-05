# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from enum import StrEnum
from typing import final


@final
class PaymentStatus(StrEnum):
    """Payment status state enumeration."""

    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


@final
class Currency(StrEnum):
    """Supported currency enumeration."""

    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'


@final
class OutboxStatus(StrEnum):
    """Outbox message status enumeration."""

    PENDING = 'pending'
    PUBLISHED = 'published'
    FAILED = 'failed'
