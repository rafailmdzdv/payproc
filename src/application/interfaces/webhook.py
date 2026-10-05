# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from typing import Any, Protocol


class WebhookSender(Protocol):
    """Client webhook notification delivery contract."""

    async def send(self, url: str, payload: dict[str, Any]) -> None:
        """Deliver webhook payload to destination URL."""
