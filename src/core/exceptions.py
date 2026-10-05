# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from typing import final


@final
class PaymentProcessingError(Exception):
    """Base exception for all domain payment errors."""


@final
class PaymentNotFoundError(Exception):
    """Raised when the requested payment cannot be found."""


@final
class DuplicatePaymentError(Exception):
    """Raised when an operation conflicts with existing idempotency state."""


@final
class GatewayExecutionError(Exception):
    """Raised when external payment gateway execution encounters an error."""


@final
class WebhookDeliveryError(Exception):
    """Raised when webhook delivery cannot be completed after retries."""
