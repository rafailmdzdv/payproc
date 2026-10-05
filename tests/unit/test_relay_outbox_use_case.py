# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from datetime import UTC, datetime

from application.use_cases.relay_outbox import RelayOutboxUseCase
from core.enums import OutboxStatus
from core.models import OutboxMessage
from tests.conftest import FakePublisher, FakeUnitOfWork


async def test_relay_outbox_success(
    fake_uow: FakeUnitOfWork,
    fake_publisher: FakePublisher,
) -> None:
    msg1 = OutboxMessage(
        id=uuid.uuid4(),
        event_type='payment.created',
        payload={'payment_id': str(uuid.uuid4())},
        status=OutboxStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    msg2 = OutboxMessage(
        id=uuid.uuid4(),
        event_type='payment.created',
        payload={'payment_id': str(uuid.uuid4())},
        status=OutboxStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    await fake_uow.outbox.add(msg1)
    await fake_uow.outbox.add(msg2)

    use_case = RelayOutboxUseCase(
        uow=fake_uow,
        publisher=fake_publisher,
        queue_name='payments.events',
    )
    dispatched_count = await use_case.execute(batch_size=10)
    pending = await fake_uow.outbox.fetch_pending(10)

    assert dispatched_count == 2
    assert len(fake_publisher.published) == 2
    assert fake_uow.committed is True
    assert len(pending) == 0


async def test_relay_outbox_empty(
    fake_uow: FakeUnitOfWork,
    fake_publisher: FakePublisher,
) -> None:
    use_case = RelayOutboxUseCase(
        uow=fake_uow,
        publisher=fake_publisher,
        queue_name='payments.events',
    )
    dispatched_count = await use_case.execute(batch_size=10)
    assert dispatched_count == 0
    assert len(fake_publisher.published) == 0


async def test_relay_outbox_publish_failure(
    fake_uow: FakeUnitOfWork,
) -> None:
    failing_publisher = FakePublisher(should_fail=True)
    msg = OutboxMessage(
        id=uuid.uuid4(),
        event_type='payment.created',
        payload={'payment_id': str(uuid.uuid4())},
        status=OutboxStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    await fake_uow.outbox.add(msg)

    use_case = RelayOutboxUseCase(
        uow=fake_uow,
        publisher=failing_publisher,
        queue_name='payments.events',
    )
    dispatched_count = await use_case.execute(batch_size=10)
    updated_msg = fake_uow._outbox.messages[msg.id]

    assert dispatched_count == 1
    assert updated_msg.retry_count == 1
    assert updated_msg.error_message is not None
    assert 'Broker connection dropped' in updated_msg.error_message
    assert updated_msg.status == OutboxStatus.PENDING
