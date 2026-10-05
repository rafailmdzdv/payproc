# Copyright © 2026 Rafail Medzhidov <rafayt323@gmail.com>
# SPDX-License-Identifier: MIT

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from application.dtos import PaymentCreateDTO
from application.use_cases.create_payment import CreatePaymentUseCase
from application.use_cases.get_payment import GetPaymentUseCase
from server.api.deps import (
    get_create_payment_use_case,
    get_payment_use_case,
    verify_api_key,
)
from server.api.schemas import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentDetailResponse,
)

MAX_IDEMPOTENCY_KEY_LEN = 255

router = APIRouter(
    prefix='/payments',
    tags=['payments'],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    '',
    status_code=status.HTTP_202_ACCEPTED,
    summary='Create a new payment',
)
async def create_payment(
    payload: PaymentCreateRequest,
    idempotency_key: Annotated[
        str,
        Header(
            alias='Idempotency-Key',
            min_length=1,
            max_length=MAX_IDEMPOTENCY_KEY_LEN,
            description='Unique request key for idempotent processing',
        ),
    ],
    use_case: Annotated[
        CreatePaymentUseCase,
        Depends(get_create_payment_use_case),
    ],
) -> PaymentCreateResponse:
    """Accept payment processing request and schedule async execution."""
    dto = PaymentCreateDTO(
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        metadata=payload.metadata,
        webhook_url=str(payload.webhook_url),
        idempotency_key=idempotency_key,
    )
    payment_dto, _ = await use_case.execute(dto)
    return PaymentCreateResponse(
        payment_id=payment_dto.id,
        status=payment_dto.status.value,
        created_at=payment_dto.created_at,
    )


@router.get(
    '/{payment_id}',
    status_code=status.HTTP_200_OK,
    summary='Get payment details',
)
async def get_payment(
    payment_id: uuid.UUID,
    use_case: Annotated[GetPaymentUseCase, Depends(get_payment_use_case)],
) -> PaymentDetailResponse:
    """Retrieve detailed state of payment by UUID."""
    payment_dto = await use_case.execute(payment_id)
    if payment_dto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Payment not found',
        )

    return PaymentDetailResponse(
        id=payment_dto.id,
        amount=payment_dto.amount,
        currency=payment_dto.currency.value,
        description=payment_dto.description,
        metadata=payment_dto.metadata,
        status=payment_dto.status.value,
        idempotency_key=payment_dto.idempotency_key,
        webhook_url=payment_dto.webhook_url,
        created_at=payment_dto.created_at,
        processed_at=payment_dto.processed_at,
    )
