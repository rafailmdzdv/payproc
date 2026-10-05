# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from typing import Final, final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_POSTGRES_PORT: Final = 5432
DEFAULT_RABBITMQ_PORT: Final = 5672
DEFAULT_APP_HOST: Final = '127.0.0.1'
DEFAULT_HTTP_PORT: Final = 8000
DEFAULT_OUTBOX_BATCH_SIZE: Final = 50
DEFAULT_MAX_RETRIES: Final = 3
DEFAULT_POLL_INTERVAL_SEC: Final = 1
DEFAULT_MIN_PROCESSING_TIME: Final = 2
DEFAULT_MAX_PROCESSING_TIME: Final = 5
DEFAULT_SUCCESS_RATE: Final = 0.9
DEFAULT_WEBHOOK_TIMEOUT_SEC: Final = 10
DEFAULT_BACKOFF_FACTOR: Final = 2


@final
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    postgres_user: str = Field(default='postgres', alias='POSTGRES_USER')
    postgres_password: str = Field(
        default='postgres',
        alias='POSTGRES_PASSWORD',
    )
    postgres_host: str = Field(default='localhost', alias='POSTGRES_HOST')
    postgres_port: int = Field(
        default=DEFAULT_POSTGRES_PORT,
        alias='POSTGRES_PORT',
    )
    postgres_db: str = Field(default='payproc', alias='POSTGRES_DB')

    rabbitmq_user: str = Field(default='guest', alias='RABBITMQ_DEFAULT_USER')
    rabbitmq_password: str = Field(
        default='guest',
        alias='RABBITMQ_DEFAULT_PASS',
    )
    rabbitmq_host: str = Field(default='localhost', alias='RABBITMQ_HOST')
    rabbitmq_port: int = Field(
        default=DEFAULT_RABBITMQ_PORT,
        alias='RABBITMQ_PORT',
    )

    api_key: str = Field(
        default='secret-static-api-key',
        alias='API_KEY',
    )

    app_host: str = Field(default=DEFAULT_APP_HOST, alias='APP_HOST')
    app_port: int = Field(default=DEFAULT_HTTP_PORT, alias='APP_PORT')

    outbox_poll_interval_sec: float = Field(
        default=DEFAULT_POLL_INTERVAL_SEC,
        alias='OUTBOX_POLL_INTERVAL_SEC',
    )
    outbox_batch_size: int = Field(
        default=DEFAULT_OUTBOX_BATCH_SIZE,
        alias='OUTBOX_BATCH_SIZE',
    )

    payment_min_processing_time: float = Field(
        default=DEFAULT_MIN_PROCESSING_TIME,
        alias='PAYMENT_MIN_PROCESSING_TIME',
    )
    payment_max_processing_time: float = Field(
        default=DEFAULT_MAX_PROCESSING_TIME,
        alias='PAYMENT_MAX_PROCESSING_TIME',
    )
    payment_success_rate: float = Field(
        default=DEFAULT_SUCCESS_RATE,
        alias='PAYMENT_SUCCESS_RATE',
    )

    webhook_timeout_sec: float = Field(
        default=DEFAULT_WEBHOOK_TIMEOUT_SEC,
        alias='WEBHOOK_TIMEOUT_SEC',
    )
    webhook_max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        alias='WEBHOOK_MAX_RETRIES',
    )
    webhook_backoff_factor: float = Field(
        default=DEFAULT_BACKOFF_FACTOR,
        alias='WEBHOOK_BACKOFF_FACTOR',
    )

    consumer_max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        alias='CONSUMER_MAX_RETRIES',
    )
    consumer_backoff_factor: float = Field(
        default=DEFAULT_BACKOFF_FACTOR,
        alias='CONSUMER_BACKOFF_FACTOR',
    )

    exchange_name: str = Field(
        default='payments',
        alias='PAYMENTS_EXCHANGE',
    )
    queue_name: str = Field(
        default='payments.new',
        alias='PAYMENTS_QUEUE',
    )
    dlx_name: str = Field(
        default='payments.dlx',
        alias='PAYMENTS_DLX',
    )
    dlq_name: str = Field(
        default='payments.dlq',
        alias='PAYMENTS_DLQ',
    )

    def database_url(self) -> str:
        """Get async PostgreSQL connection URL."""
        return (
            f'postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}'
            f'@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}'
        )

    def rabbitmq_url(self) -> str:
        """Get RabbitMQ AMQP connection URL."""
        return f'amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/'


settings = Settings()
