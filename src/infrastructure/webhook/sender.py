# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from typing import Any, Final, final, override

import httpx

from application.interfaces.webhook import WebhookSender
from core.exceptions import WebhookDeliveryError
from infrastructure.config import settings

logger = logging.getLogger(__name__)

INITIAL_RETRY_ATTEMPT: Final = 1


@final
class HttpWebhookSender(WebhookSender):
    """Delivers client webhook notifications over HTTP with exponential retry."""

    def __init__(
        self,
        max_retries: int = settings.webhook_max_retries,
        backoff_factor: float = settings.webhook_backoff_factor,
        timeout_sec: float = settings.webhook_timeout_sec,
    ) -> None:
        """Initialize webhook sender with retry parameters."""
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._timeout_sec = timeout_sec

    @override
    async def send(self, url: str, payload: dict[str, Any]) -> None:
        """Send notification to webhook destination with exponential retry."""
        async with httpx.AsyncClient(timeout=self._timeout_sec) as client:
            attempt = INITIAL_RETRY_ATTEMPT
            while attempt <= self._max_retries:
                if await self._try_dispatch(client, url, payload, attempt):
                    return

                if attempt < self._max_retries:
                    retry_delay = self._backoff_factor ** (attempt - 1)
                    await asyncio.sleep(retry_delay)
                attempt += 1

        raise WebhookDeliveryError(
            f'Failed to deliver webhook to {url} after {self._max_retries} attempts',
        )

    async def _try_dispatch(
        self,
        client: httpx.AsyncClient,
        url: str,
        payload: dict[str, Any],
        attempt: int,
    ) -> bool:
        """Attempt single dispatch and catch connection errors."""
        try:
            return await self._dispatch_attempt(client, url, payload, attempt)
        except httpx.HTTPError as net_error:
            logger.warning(
                'Webhook HTTP error on attempt %d/%d: %s',
                attempt,
                self._max_retries,
                str(net_error),
            )
            return False

    async def _dispatch_attempt(
        self,
        client: httpx.AsyncClient,
        url: str,
        payload: dict[str, Any],
        attempt: int,
    ) -> bool:
        """Execute single webhook HTTP request."""
        response = await client.post(url, json=payload)
        if response.is_success:
            logger.info(
                'Webhook delivered successfully to %s on attempt %d',
                url,
                attempt,
            )
            return True

        logger.warning(
            'Webhook endpoint returned status %d on attempt %d/%d',
            response.status_code,
            attempt,
            self._max_retries,
        )
        return False
