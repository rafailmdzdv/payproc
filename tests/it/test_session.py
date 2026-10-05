# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infrastructure.database.session import get_db_session


async def test_get_db_session_success(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    with patch(
        'infrastructure.database.session.async_session_factory',
        db_session_factory,
    ):
        gen = get_db_session()
        session = await anext(gen)
        assert isinstance(session, AsyncSession)
        with pytest.raises(StopAsyncIteration):
            await anext(gen)


async def test_get_db_session_error(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    with patch(
        'infrastructure.database.session.async_session_factory',
        db_session_factory,
    ):
        gen = get_db_session()
        await anext(gen)
        with pytest.raises(ValueError, match='Session error'):
            await gen.athrow(ValueError('Session error'))
