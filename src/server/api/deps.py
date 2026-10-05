# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from application.interfaces.uow import UnitOfWork
from application.use_cases.create_payment import CreatePaymentUseCase
from application.use_cases.get_payment import GetPaymentUseCase
from infrastructure.config import settings
from infrastructure.database.session import async_session_factory
from infrastructure.database.uow import SqlUnitOfWork


async def verify_api_key(
    api_key_header: str | None = Header(
        default=None,
        alias='X-API-Key',
        description='Static authorization key',
    ),
) -> str:
    """Validate static API key provided in request headers."""
    if api_key_header is None or api_key_header != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or missing API key',
        )
    return api_key_header


def get_uow() -> UnitOfWork:
    """Provide Unit of Work instance for transactional operations."""
    return SqlUnitOfWork(session_factory=async_session_factory)


def get_create_payment_use_case(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CreatePaymentUseCase:
    """Provide CreatePaymentUseCase instance with injected Unit of Work."""
    return CreatePaymentUseCase(uow=uow)


def get_payment_use_case(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> GetPaymentUseCase:
    """Provide GetPaymentUseCase instance with injected Unit of Work."""
    return GetPaymentUseCase(uow=uow)
