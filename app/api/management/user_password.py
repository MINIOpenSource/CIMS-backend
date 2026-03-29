"""密码管理路由。

提供密码修改（需旧密码验证）。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.models.session import get_db
from app.models.user import User
from app.services.crypto.hasher import hash_password, verify_password
from app.api.schemas.profile import PasswordChange

router = APIRouter()


@router.post("/change")
async def change_password(
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    """修改密码（需验证旧密码）。"""
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")
    if not verify_password(body.old_password, user.hashed_password):
        raise HTTPException(400, "旧密码错误")
    user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"message": "密码已修改"}


@router.post("/reset")
async def reset_password(
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    """重置密码（自助流程，暂未实现详细逻辑）。"""
    return {"message": "暂未实现"}
