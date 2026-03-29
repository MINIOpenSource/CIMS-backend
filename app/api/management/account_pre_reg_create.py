"""预注册客户端创建路由。"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.pre_reg import PreRegCreate, PreRegOut
from app.models.pre_registered_client import PreRegisteredClient
from app.models.session import get_db
from .account_pre_reg_crud import _to_out

router = APIRouter()


@router.post("/create", response_model=PreRegOut, status_code=201)
async def create_pre_reg(
    account_id: str,
    body: PreRegCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建预注册客户端。校验 class_identity 唯一性。"""
    dup = await db.execute(
        select(PreRegisteredClient).where(
            PreRegisteredClient.account_id == account_id,
            PreRegisteredClient.class_identity == body.class_identity,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(400, "该 class_identity 已存在")
    p = PreRegisteredClient(
        id=str(uuid.uuid4()),
        account_id=account_id,
        label=body.label,
        class_identity=body.class_identity,
        created_at=datetime.now(timezone.utc),
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _to_out(p)
