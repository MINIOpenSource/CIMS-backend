"""访问控制 — 修改成员角色。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.access import AccessMemberOut, AccessRoleUpdate
from app.core.auth.dependencies import get_current_user_id
from app.models.account_member import AccountMember
from app.models.session import get_db
from .account_access import _member_out

router = APIRouter()


@router.post("/{user_id}", response_model=AccessMemberOut)
async def update_access(
    account_id: str,
    user_id: str,
    body: AccessRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """修改成员的账户内角色。"""
    m = (
        await db.execute(
            select(AccountMember).where(
                AccountMember.id == user_id,
                AccountMember.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(404, "成员记录不存在")
    m.role_in_account = body.role_in_account
    await db.commit()
    await db.refresh(m)
    return _member_out(m)
