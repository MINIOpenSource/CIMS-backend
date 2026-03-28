"""配对码管理路由。

提供配对码的列表和搜索接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant.context import get_tenant_id
from app.models.session import get_db
from app.models.pairing import PairingCode
from app.api.schemas.pairing import PairingCodeOut

router = APIRouter()


@router.get("/list", response_model=list[PairingCodeOut])
async def list_pairing_codes(
    db: AsyncSession = Depends(get_db),
):
    """列出当前账户的配对码。"""
    tid = get_tenant_id()
    if not tid:
        raise HTTPException(400, "租户上下文缺失")
    rows = (
        await db.execute(
            select(PairingCode).where(PairingCode.tenant_id == tid)
        )
    ).scalars().all()
    return [
        PairingCodeOut(
            id=r.id,
            code=r.code,
            client_uid=getattr(r, "client_uid", ""),
            approved=getattr(r, "approved", False),
            used=getattr(r, "used", False),
            created_at=str(getattr(r, "created_at", "")),
        )
        for r in rows
    ]


@router.get("/search", response_model=list[PairingCodeOut])
async def search_pairing_codes(
    q: str = "", db: AsyncSession = Depends(get_db)
):
    """搜索配对码。"""
    tid = get_tenant_id()
    if not tid:
        raise HTTPException(400, "租户上下文缺失")
    rows = (
        await db.execute(
            select(PairingCode).where(PairingCode.tenant_id == tid)
        )
    ).scalars().all()
    results = [
        PairingCodeOut(
            id=r.id, code=r.code,
            client_uid=getattr(r, "client_uid", ""),
            approved=getattr(r, "approved", False),
            used=getattr(r, "used", False),
            created_at=str(getattr(r, "created_at", "")),
        )
        for r in rows
        if not q or q.lower() in (r.code or "").lower()
    ]
    return results


@router.post("/enable")
async def enable_pairing():
    """启用配对码功能。"""
    return {"message": "暂未实现"}


@router.post("/disable")
async def disable_pairing():
    """禁用配对码功能。"""
    return {"message": "暂未实现"}
