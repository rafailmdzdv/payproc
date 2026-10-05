# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from typing import Any, Protocol


class MessagePublisher(Protocol):
    """Message broker publication contract."""

    async def publish(self, queue_name: str, payload: dict[str, Any]) -> None:
        """Publish payload message to target queue."""
