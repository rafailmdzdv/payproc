# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import asyncio
import logging
import random
import uuid
from decimal import Decimal
from typing import final, override

from application.interfaces.gateway import PaymentGateway
from core.enums import Currency, PaymentStatus
from infrastructure.config import settings

logger = logging.getLogger(__name__)


@final
class GatewayEmulator(PaymentGateway):
    """Emulates processing via external payment provider."""

    def __init__(
        self,
        min_delay: float = settings.payment_min_processing_time,
        max_delay: float = settings.payment_max_processing_time,
        success_rate: float = settings.payment_success_rate,
    ) -> None:
        """Initialize gateway emulator with timing and probability parameters."""
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._success_rate = success_rate

    @override
    async def execute(
        self,
        payment_id: uuid.UUID,
        amount: Decimal,
        currency: Currency,
    ) -> PaymentStatus:
        """Emulate external gateway processing with configurable delay and outcome."""
        delay = random.uniform(self._min_delay, self._max_delay)  # noqa: S311
        logger.info(
            'Gateway processing payment %s (%.2f %s) for %.2f seconds',
            str(payment_id),
            amount,
            currency.value,
            delay,
        )
        await asyncio.sleep(delay)

        is_success = random.random() < self._success_rate  # noqa: S311
        if is_success:
            return PaymentStatus.SUCCEEDED
        return PaymentStatus.FAILED
