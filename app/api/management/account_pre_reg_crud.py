"""预注册客户端 CRUD 路由。"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.pre_reg import PreRegCreate, PreRegOut
from app.models.pre_registered_client import PreRegisteredClient
from app.models.session import get_db

router = APIRouter()


def _to_out(p: PreRegisteredClient) -> PreRegOut:
    """转换模型为响应。"""
    return PreRegOut(
        id=p.id,
        account_id=p.account_id,
        label=p.label,
        class_identity=p.class_identity,
        created_at=str(p.created_at),
    )


@router.get("/list", response_model=list[PreRegOut])
async def list_pre_regs(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """列出预注册客户端。"""
    rows = (
        await db.execute(
            select(PreRegisteredClient).where(
                PreRegisteredClient.account_id == account_id
            )
        )
    ).scalars().all()
    return [_to_out(r) for r in rows]


@router.get("/search", response_model=list[PreRegOut])
async def search_pre_regs(
    account_id: str,
    q: str = "",
    db: AsyncSession = Depends(get_db),
):
    """搜索预注册客户端。"""
    rows = (
        await db.execute(
            select(PreRegisteredClient).where(
                PreRegisteredClient.account_id == account_id
            )
        )
    ).scalars().all()
    if not q:
        return [_to_out(r) for r in rows]
    return [
        _to_out(r) for r in rows
        if q.lower() in (r.class_identity or "").lower()
    ]
