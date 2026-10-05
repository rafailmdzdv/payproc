# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from decimal import Decimal
from typing import Protocol

from core.enums import Currency, PaymentStatus


class PaymentGateway(Protocol):
    """External payment processing gateway contract."""

    async def execute(
        self,
        payment_id: uuid.UUID,
        amount: Decimal,
        currency: Currency,
    ) -> PaymentStatus:
        """Process transaction through payment gateway."""
