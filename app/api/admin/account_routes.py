"""超管账户路由。

复用 Management API 的 /account 接口，以超管身份操作。
支持 ?role={user_id} 以某个用户身份操作。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.account_out import AccountOut
from app.core.auth.dependencies import require_role
from app.models.account import Account
from app.models.session import get_db

router = APIRouter()
_sa = require_role(100)


@router.get("", response_model=list[AccountOut])
async def list_all_accounts(
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """列出所有账户（超管）。"""
    rows = (await db.execute(select(Account))).scalars().all()
    return [
        AccountOut(
            id=a.id,
            name=a.name,
            slug=a.slug,
            api_key=a.api_key,
            is_active=a.is_active,
            created_at=str(a.created_at),
        )
        for a in rows
    ]
