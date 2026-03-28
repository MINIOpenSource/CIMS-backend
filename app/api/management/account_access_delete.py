"""访问控制 — 移除成员。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.models.account_member import AccountMember
from app.models.session import get_db

router = APIRouter()


@router.delete("/{user_id}", status_code=204)
async def delete_access(
    account_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """移除账户成员。"""
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
    await db.delete(m)
    await db.commit()
