# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import pytest
from fastapi import HTTPException

from infrastructure.config import settings
from server.api.deps import verify_api_key


async def test_verify_api_key_valid() -> None:
    key = await verify_api_key(settings.api_key)
    assert key == settings.api_key


async def test_verify_api_key_invalid_string() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key('wrong_key')
    assert exc_info.value.status_code == 401


async def test_verify_api_key_missing_none() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(None)
    assert exc_info.value.status_code == 401
