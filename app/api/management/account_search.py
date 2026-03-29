"""账户列表辅助路由。

提供搜索和创建账户接口。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.account_out import AccountOut
from app.core.auth.dependencies import get_current_user_id
from app.models.account import Account
from app.models.account_member import AccountMember
from app.models.session import get_db
from .account_helpers import _out

router = APIRouter()


@router.post("/search", response_model=list[AccountOut])
async def search_accounts(
    q: str = "",
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """按名称搜索当前用户可见的账户。"""
    stmt = (
        select(Account)
        .join(AccountMember, Account.id == AccountMember.account_id)
        .where(AccountMember.user_id == user_id)
        .where(Account.name.ilike(f"%{q}%"))
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_out(a) for a in rows]
