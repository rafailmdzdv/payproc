# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infrastructure.config import settings
from infrastructure.database.uow import SqlUnitOfWork
from server.api.app import app
from server.api.deps import get_uow


def _build_payload() -> dict[str, Any]:
    return {
        'amount': '100.50',
        'currency': 'RUB',
        'description': 'API payment test',
        'metadata': {'test': True},
        'webhook_url': 'https://callback.com/webhook',
    }


@pytest.fixture
async def api_client(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[httpx.AsyncClient]:
    app.dependency_overrides[get_uow] = lambda: SqlUnitOfWork(db_session_factory)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        yield client
    app.dependency_overrides.clear()


async def test_health_check() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        resp = await client.get('/health')
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {'status': 'ok'}


async def test_create_payment_success(api_client: httpx.AsyncClient) -> None:
    headers = {
        'X-API-Key': settings.api_key,
        'Idempotency-Key': 'key_create_001',
    }
    resp = await api_client.post(
        '/api/v1/payments',
        json=_build_payload(),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_202_ACCEPTED
    body = resp.json()
    assert 'payment_id' in body
    assert body['status'] == 'pending'


async def test_create_payment_duplicate_idempotency(
    api_client: httpx.AsyncClient,
) -> None:
    headers = {
        'X-API-Key': settings.api_key,
        'Idempotency-Key': 'key_idemp_duplicate',
    }
    first_resp = await api_client.post(
        '/api/v1/payments',
        json=_build_payload(),
        headers=headers,
    )
    assert first_resp.status_code == status.HTTP_202_ACCEPTED
    first_id = first_resp.json()['payment_id']

    second_resp = await api_client.post(
        '/api/v1/payments',
        json=_build_payload(),
        headers=headers,
    )
    assert second_resp.status_code == status.HTTP_202_ACCEPTED
    assert second_resp.json()['payment_id'] == first_id


async def test_get_payment_success(api_client: httpx.AsyncClient) -> None:
    headers = {
        'X-API-Key': settings.api_key,
        'Idempotency-Key': 'key_get_001',
    }
    create_resp = await api_client.post(
        '/api/v1/payments',
        json=_build_payload(),
        headers=headers,
    )
    payment_id = create_resp.json()['payment_id']

    get_resp = await api_client.get(
        f'/api/v1/payments/{payment_id}',
        headers={'X-API-Key': settings.api_key},
    )
    assert get_resp.status_code == status.HTTP_200_OK
    detail = get_resp.json()
    assert detail['id'] == payment_id
    assert detail['amount'] == '100.50'
    assert detail['currency'] == 'RUB'
    assert detail['status'] == 'pending'


async def test_get_payment_not_found(api_client: httpx.AsyncClient) -> None:
    missing_id = str(uuid.uuid4())
    resp = await api_client.get(
        f'/api/v1/payments/{missing_id}',
        headers={'X-API-Key': settings.api_key},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_create_payment_missing_api_key(
    api_client: httpx.AsyncClient,
) -> None:
    resp = await api_client.post(
        '/api/v1/payments',
        json=_build_payload(),
        headers={'Idempotency-Key': 'key_no_auth'},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_payment_invalid_api_key(
    api_client: httpx.AsyncClient,
) -> None:
    resp = await api_client.post(
        '/api/v1/payments',
        json=_build_payload(),
        headers={'X-API-Key': 'invalid_key', 'Idempotency-Key': 'key_bad_auth'},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_payment_missing_idempotency_key(
    api_client: httpx.AsyncClient,
) -> None:
    resp = await api_client.post(
        '/api/v1/payments',
        json=_build_payload(),
        headers={'X-API-Key': settings.api_key},
    )
    assert resp.status_code == 422
