# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from types import TracebackType
from typing import Protocol, Self

from application.interfaces.repositories import (
    OutboxRepository,
    PaymentRepository,
)


class UnitOfWork(Protocol):
    """Transactional boundary coordinating repositories."""

    def payments(self) -> PaymentRepository:
        """Payment repository instance."""

    def outbox(self) -> OutboxRepository:
        """Outbox repository instance."""

    async def commit(self) -> None:
        """Commit current transaction."""

    async def rollback(self) -> None:
        """Rollback current transaction."""

    async def __aenter__(self) -> Self:
        """Enter transactional context."""

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit transactional context and handle rollback on exception."""
