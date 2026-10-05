# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from unittest.mock import AsyncMock, patch

from faststream.rabbit import TestRabbitBroker

from infrastructure.broker import rabbit as rabbit_broker
from infrastructure.broker.rabbit import RabbitMessagePublisher
from server.consumer import worker as consumer_worker


async def test_consumer_success() -> None:
    payment_id = uuid.uuid4()
    async with TestRabbitBroker(rabbit_broker.broker) as br:
        with patch.object(consumer_worker, '_get_process_use_case') as mock_factory:
            mock_use_case = AsyncMock()
            mock_factory.return_value = mock_use_case

            await br.publish(
                {'payment_id': str(payment_id)},
                queue=rabbit_broker.main_queue,
            )

            assert mock_use_case.execute.call_count == 1
            mock_use_case.execute.assert_called_once_with(payment_id)


async def test_consumer_retry_and_dlq() -> None:
    payment_id = uuid.uuid4()
    async with TestRabbitBroker(rabbit_broker.broker) as br:
        with (
            patch.object(consumer_worker, '_get_process_use_case') as mock_factory,
            patch('asyncio.sleep', new_callable=AsyncMock),
            patch.object(consumer_worker, '_route_to_dlq', new_callable=AsyncMock) as mock_dlq,
        ):
            mock_use_case = AsyncMock()
            mock_use_case.execute.side_effect = RuntimeError('Processing crashed')
            mock_factory.return_value = mock_use_case

            await br.publish(
                {'payment_id': str(payment_id)},
                queue=rabbit_broker.main_queue,
            )

            assert mock_use_case.execute.call_count == 3
            assert mock_dlq.call_count == 1


async def test_consumer_missing_payment_id() -> None:
    async with TestRabbitBroker(rabbit_broker.broker) as br:
        with patch.object(consumer_worker, '_get_process_use_case') as mock_factory:
            mock_use_case = AsyncMock()
            mock_factory.return_value = mock_use_case

            await br.publish(
                {'amount': '100.00'},
                queue=rabbit_broker.main_queue,
            )

            assert mock_use_case.execute.call_count == 0


async def test_dlq_subscriber_handles_message() -> None:
    async with TestRabbitBroker(rabbit_broker.broker) as br:
        dlq_payload = {
            'original_payload': {'payment_id': str(uuid.uuid4())},
            'error': 'Timeout',
        }
        await br.publish(dlq_payload, queue=rabbit_broker.dlq_queue)


async def test_rabbit_message_publisher() -> None:
    async with TestRabbitBroker(rabbit_broker.broker) as br:
        with patch.object(consumer_worker, '_get_process_use_case') as mock_factory:
            mock_use_case = AsyncMock()
            mock_factory.return_value = mock_use_case

            publisher = RabbitMessagePublisher(br)
            payment_id = uuid.uuid4()
            await publisher.publish(
                rabbit_broker.main_queue.name,
                {'payment_id': str(payment_id)},
            )

            assert mock_use_case.execute.call_count == 1


async def test_setup_broker() -> None:
    mock_broker = AsyncMock()
    await rabbit_broker.setup_broker(mock_broker)
    assert mock_broker.declare_exchange.call_count == 2
    assert mock_broker.declare_queue.call_count == 2


async def test_consumer_on_startup() -> None:
    with patch('server.consumer.worker.rabbit_broker.setup_broker', new_callable=AsyncMock) as mock_setup:
        await consumer_worker.after_startup()
        assert mock_setup.call_count == 1


async def test_route_to_dlq() -> None:
    with patch('server.consumer.worker.rabbit_broker.broker.publish', new_callable=AsyncMock) as mock_pub:
        await consumer_worker._route_to_dlq({'payment_id': '123'}, 'Network failure')
        assert mock_pub.call_count == 1
