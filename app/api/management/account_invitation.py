"""邀请管理路由 — 列出与辅助。

提供邀请列表查询和模型转换辅助。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.invitation import InvitationOut
from app.core.auth.dependencies import get_current_user_id
from app.models.invitation import Invitation
from app.models.session import get_db

router = APIRouter()


def _out(inv: Invitation) -> InvitationOut:
    """模型转响应。"""
    return InvitationOut(
        id=inv.id, account_id=inv.account_id,
        inviter_user_id=inv.inviter_user_id, code=inv.code,
        role_in_account=inv.role_in_account,
        max_uses=inv.max_uses, used_count=inv.used_count,
        expires_at=str(inv.expires_at) if inv.expires_at else None,
        is_active=inv.is_active, created_at=str(inv.created_at),
    )


@router.get("/list", response_model=list[InvitationOut])
async def list_invitations(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """列出账户下的邀请。"""
    rows = (
        await db.execute(
            select(Invitation).where(
                Invitation.account_id == account_id
            )
        )
    ).scalars().all()
    return [_out(inv) for inv in rows]


@router.get("/search", response_model=list[InvitationOut])
async def search_invitations(
    account_id: str,
    q: str = "",
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """搜索邀请。"""
    rows = (
        await db.execute(
            select(Invitation).where(
                Invitation.account_id == account_id
            )
        )
    ).scalars().all()
    if not q:
        return [_out(inv) for inv in rows]
    return [
        _out(inv) for inv in rows
        if q.lower() in (inv.code or "").lower()
    ]


@router.post("/{invitation_id}/rename")
async def rename_invitation(account_id: str, invitation_id: str):
    """重命名邀请。"""
    return {"message": "暂未实现"}


@router.get("/{invitation_id}")
async def get_invitation(
    account_id: str,
    invitation_id: str,
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """获取邀请信息。"""
    inv = (
        await db.execute(
            select(Invitation).where(
                Invitation.id == invitation_id,
                Invitation.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not inv:
        from fastapi import HTTPException
        raise HTTPException(404, "邀请不存在")
    return _out(inv)
