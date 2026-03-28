"""邀请撤销路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.models.invitation import Invitation
from app.models.session import get_db

router = APIRouter()


@router.delete("/{invitation_id}")
async def revoke_invitation(
    account_id: str,
    invitation_id: str,
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """撤销指定邀请码。"""
    inv = (
        await db.execute(
            select(Invitation).where(
                Invitation.id == invitation_id,
                Invitation.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "邀请不存在")
    inv.is_active = False
    await db.commit()
    return {"message": f"邀请 {invitation_id} 已撤销"}
