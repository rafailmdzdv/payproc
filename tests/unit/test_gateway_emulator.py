# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from decimal import Decimal

from core.enums import Currency, PaymentStatus
from infrastructure.gateway.emulator import GatewayEmulator

ZERO: float = float(0)
ONE: float = float(1)


async def test_gateway_emulator_always_success() -> None:
    emulator = GatewayEmulator(min_delay=ZERO, max_delay=ZERO, success_rate=ONE)
    outcome = await emulator.execute(
        payment_id=uuid.uuid4(),
        amount=Decimal('10.00'),
        currency=Currency.RUB,
    )
    assert outcome == PaymentStatus.SUCCEEDED


async def test_gateway_emulator_always_fail() -> None:
    emulator = GatewayEmulator(min_delay=ZERO, max_delay=ZERO, success_rate=ZERO)
    outcome = await emulator.execute(
        payment_id=uuid.uuid4(),
        amount=Decimal('10.00'),
        currency=Currency.USD,
    )
    assert outcome == PaymentStatus.FAILED
