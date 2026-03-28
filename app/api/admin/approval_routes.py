"""管理员用户审核路由。

提供 Pending 用户列表、审核通过和拒绝的端点。
路径改为 /user/pending/* 以符合 NewAPI.md。
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.user_out import UserOut
from app.core.auth.dependencies import require_role
from app.models.session import get_db
from app.services.user.approval import (
    list_pending_users,
    reject_user,
)
from app.services.user.approval_approve import approve_user
from .user_helpers import _to_out
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
_sa = require_role(100)


@router.get("/list", response_model=list[UserOut])
async def get_pending_users(
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """列出所有待审核用户。"""
    users = await list_pending_users(db, offset=offset, limit=limit)
    return [_to_out(u) for u in users]


@router.post("/approve/{user_id}", response_model=UserOut)
async def approve_pending(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """批准用户。"""
    user = await approve_user(user_id, db)
    if not user:
        raise HTTPException(404, "用户不存在或非待审核状态")
    return _to_out(user)


@router.post("/reject/{user_id}")
async def reject_pending(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """拒绝用户。"""
    ok = await reject_user(user_id, db)
    if not ok:
        raise HTTPException(404, "用户不存在或非待审核状态")
    return {"message": "已拒绝"}
