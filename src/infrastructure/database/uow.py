# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from types import TracebackType
from typing import Self, final, override

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.interfaces.repositories import (
    OutboxRepository,
    PaymentRepository,
)
from application.interfaces.uow import UnitOfWork
from infrastructure.database.repositories import (
    SqlOutboxRepository,
    SqlPaymentRepository,
)


@final
class SqlUnitOfWork(UnitOfWork):
    """SQLAlchemy implementation of Unit of Work pattern."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Initialize UoW with session factory."""
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._payments: PaymentRepository | None = None
        self._outbox: OutboxRepository | None = None

    @property
    @override
    def payments(self) -> PaymentRepository:
        """Access payment repository within active context."""
        if self._payments is None:
            raise RuntimeError('Unit of Work has not been entered')
        return self._payments

    @property
    @override
    def outbox(self) -> OutboxRepository:
        """Access outbox repository within active context."""
        if self._outbox is None:
            raise RuntimeError('Unit of Work has not been entered')
        return self._outbox

    @override
    async def commit(self) -> None:
        """Commit current transaction."""
        if self._session is not None:
            await self._session.commit()

    @override
    async def rollback(self) -> None:
        """Rollback current transaction."""
        if self._session is not None:
            await self._session.rollback()

    @override
    async def __aenter__(self) -> Self:
        """Open session and instantiate repositories."""
        self._session = self._session_factory()
        self._payments = SqlPaymentRepository(self._session)
        self._outbox = SqlOutboxRepository(self._session)
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Rollback on exception and close session."""
        if self._session is not None:
            if exc_type is not None:
                await self._session.rollback()
            await self._session.close()
            self._session = None
            self._payments = None
            self._outbox = None
