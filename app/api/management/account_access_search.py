"""访问控制 — 按 user_id 搜索成员。"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.access import AccessMemberOut
from app.core.auth.dependencies import get_current_user_id
from app.models.account_member import AccountMember
from app.models.session import get_db
from .account_access import _member_out

router = APIRouter()


@router.get("/search", response_model=list[AccessMemberOut])
async def search_access(
    account_id: str,
    q: str = "",
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """按 user_id 搜索账户成员。"""
    stmt = select(AccountMember).where(
        AccountMember.account_id == account_id,
        AccountMember.user_id.ilike(f"%{q}%"),
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_member_out(m) for m in rows]
