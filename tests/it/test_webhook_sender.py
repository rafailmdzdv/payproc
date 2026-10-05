# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.exceptions import WebhookDeliveryError
from infrastructure.webhook.sender import HttpWebhookSender


async def test_webhook_dispatch_success() -> None:
    mock_response = MagicMock()
    mock_response.is_success = True

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        sender = HttpWebhookSender(max_retries=2, backoff_factor=0.01, timeout_sec=1.0)
        await sender.send('https://mock.hook/api', {'status': 'succeeded'})

        assert mock_post.call_count == 1


async def test_webhook_dispatch_retry_then_success() -> None:
    fail_response = MagicMock()
    fail_response.is_success = False
    fail_response.status_code = 500

    success_response = MagicMock()
    success_response.is_success = True

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [fail_response, success_response]
        sender = HttpWebhookSender(max_retries=3, backoff_factor=0.01, timeout_sec=1.0)
        await sender.send('https://mock.hook/api', {'status': 'succeeded'})

        assert mock_post.call_count == 2


async def test_webhook_dispatch_exhaustion_raises() -> None:
    fail_response = MagicMock()
    fail_response.is_success = False
    fail_response.status_code = 502

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fail_response
        sender = HttpWebhookSender(max_retries=2, backoff_factor=0.01, timeout_sec=1.0)

        with pytest.raises(WebhookDeliveryError):
            await sender.send('https://mock.hook/api', {'status': 'failed'})

        assert mock_post.call_count == 2


async def test_webhook_dispatch_network_exception() -> None:
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError('Network unreachable')
        sender = HttpWebhookSender(max_retries=2, backoff_factor=0.01, timeout_sec=1.0)

        with pytest.raises(WebhookDeliveryError):
            await sender.send('https://mock.hook/api', {'status': 'pending'})

        assert mock_post.call_count == 2
