"""超管用户密码管理路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.profile import PasswordReset, PasswordChange
from app.core.auth.dependencies import require_role
from app.models.session import get_db
from app.models.user import User
from app.services.crypto.hasher import hash_password, verify_password

router = APIRouter()
_sa = require_role(100)


@router.post("/{user_id}/password/reset")
async def reset_password(
    user_id: str,
    body: PasswordReset,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """重置用户密码（无需旧密码）。"""
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "密码已重置"}


@router.post("/{user_id}/password/change")
async def change_password(
    user_id: str,
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """超管修改用户密码（需验证旧密码）。"""
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")
    if not verify_password(body.old_password, user.hashed_password):
        raise HTTPException(400, "旧密码错误")
    user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "密码已修改"}
