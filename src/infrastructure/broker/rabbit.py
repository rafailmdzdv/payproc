# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from typing import Any, final, override

from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)

from application.interfaces.broker import MessagePublisher
from infrastructure.config import settings

payments_exchange = RabbitExchange(
    name=settings.exchange_name,
    type=ExchangeType.DIRECT,
    durable=True,
)

dlx_exchange = RabbitExchange(
    name=settings.dlx_name,
    type=ExchangeType.DIRECT,
    durable=True,
)

dlq_queue = RabbitQueue(
    name=settings.dlq_name,
    durable=True,
    routing_key=settings.dlq_name,
)

main_queue = RabbitQueue(
    name=settings.queue_name,
    durable=True,
    routing_key=settings.queue_name,
    arguments={
        'x-dead-letter-exchange': settings.dlx_name,
        'x-dead-letter-routing-key': settings.dlq_name,
    },
)

broker = RabbitBroker(url=settings.rabbitmq_url())


async def setup_broker(rabbit_broker: RabbitBroker) -> None:
    """Declare exchanges, queues, and dead-letter routing on RabbitMQ."""
    await rabbit_broker.declare_exchange(dlx_exchange)
    await rabbit_broker.declare_queue(dlq_queue)
    await rabbit_broker.declare_exchange(payments_exchange)
    await rabbit_broker.declare_queue(main_queue)


@final
class RabbitMessagePublisher(MessagePublisher):
    """RabbitMQ message publisher."""

    def __init__(self, rabbit_broker: RabbitBroker) -> None:
        """Initialize publisher with FastStream broker instance."""
        self._broker = rabbit_broker

    @override
    async def publish(self, queue_name: str, payload: dict[str, Any]) -> None:
        """Publish message payload to specified queue."""
        await self._broker.publish(payload, queue=queue_name)
