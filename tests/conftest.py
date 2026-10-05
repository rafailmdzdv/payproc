# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Any, Self, final, override

import pytest

from application.interfaces import (
    broker,
    gateway,
    repositories,
    uow,
    webhook,
)
from core.enums import Currency, OutboxStatus, PaymentStatus
from core.models import OutboxMessage, Payment

DispatchedItem = tuple[str, dict[str, Any]]
PublishedItem = tuple[str, dict[str, Any]]
GatewayCall = tuple[uuid.UUID, Decimal, Currency]


@final
class FakePaymentRepository(repositories.PaymentRepository):
    """PaymentRepository stub."""

    def __init__(self) -> None:
        self.payments_by_id: dict[uuid.UUID, Payment] = {}
        self.payments_by_idempotency: dict[str, Payment] = {}

    @override
    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        return self.payments_by_id.get(payment_id)

    @override
    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        return self.payments_by_idempotency.get(idempotency_key)

    @override
    async def add(self, payment: Payment) -> None:
        self.payments_by_id[payment.id] = payment
        self.payments_by_idempotency[payment.idempotency_key] = payment

    @override
    async def update_status(
        self,
        payment_id: uuid.UUID,
        status: PaymentStatus,
        processed_at: datetime,
    ) -> Payment:
        current = self.payments_by_id.get(payment_id)
        if current is None:
            raise KeyError(payment_id)
        updated = replace(current, status=status, processed_at=processed_at)
        self.payments_by_id[payment_id] = updated
        self.payments_by_idempotency[updated.idempotency_key] = updated
        return updated


@final
class FakeOutboxRepository(repositories.OutboxRepository):
    """OutboxRepository stub."""

    def __init__(self) -> None:
        self.messages: dict[uuid.UUID, OutboxMessage] = {}

    @override
    async def add(self, message: OutboxMessage) -> None:
        self.messages[message.id] = message

    @override
    async def fetch_pending(self, limit: int) -> list[OutboxMessage]:
        pending = [msg for msg in self.messages.values() if msg.status == OutboxStatus.PENDING]
        return pending[:limit]

    @override
    async def mark_published(self, message_id: uuid.UUID, published_at: datetime) -> None:
        msg = self.messages.get(message_id)
        if msg is not None:
            self.messages[message_id] = replace(
                msg,
                status=OutboxStatus.PUBLISHED,
                published_at=published_at,
            )

    @override
    async def increment_retry(self, message_id: uuid.UUID, error_message: str) -> None:
        msg = self.messages.get(message_id)
        if msg is not None:
            self.messages[message_id] = replace(
                msg,
                retry_count=msg.retry_count + 1,
                error_message=error_message,
            )


@final
class FakeUnitOfWork(uow.UnitOfWork):
    """UnitOfWork stub."""

    def __init__(self) -> None:
        self._payments = FakePaymentRepository()
        self._outbox = FakeOutboxRepository()
        self.committed = False
        self.rolled_back = False

    @override
    def payments(self) -> repositories.PaymentRepository:
        return self._payments

    @override
    def outbox(self) -> repositories.OutboxRepository:
        return self._outbox

    @override
    async def commit(self) -> None:
        self.committed = True

    @override
    async def rollback(self) -> None:
        self.rolled_back = True

    @override
    async def __aenter__(self) -> Self:
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()


@final
class FakeGateway(gateway.PaymentGateway):
    """PaymentGateway stub."""

    def __init__(self, desired_outcome: PaymentStatus = PaymentStatus.SUCCEEDED) -> None:
        self.outcome = desired_outcome
        self.calls: list[GatewayCall] = []

    @override
    async def execute(
        self,
        payment_id: uuid.UUID,
        amount: Decimal,
        currency: Currency,
    ) -> PaymentStatus:
        self.calls.append((payment_id, amount, currency))
        return self.outcome


@final
class FakeWebhookSender(webhook.WebhookSender):
    """WebhookSender stub."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.dispatched: list[DispatchedItem] = []

    @override
    async def send(self, url: str, payload: dict[str, Any]) -> None:
        if self.should_fail:
            raise RuntimeError('Webhook endpoint unreachable')
        self.dispatched.append((url, payload))


@final
class FakePublisher(broker.MessagePublisher):
    """MessagePublisher stub."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.published: list[PublishedItem] = []

    @override
    async def publish(self, queue_name: str, message: dict[str, Any]) -> None:
        if self.should_fail:
            raise RuntimeError('Broker connection dropped')
        self.published.append((queue_name, message))


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def fake_gateway() -> FakeGateway:
    return FakeGateway()


@pytest.fixture
def fake_webhook() -> FakeWebhookSender:
    return FakeWebhookSender()


@pytest.fixture
def fake_publisher() -> FakePublisher:
    return FakePublisher()
