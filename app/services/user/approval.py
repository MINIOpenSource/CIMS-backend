"""用户审核服务 — 查询与拒绝。

提供 Pending 用户列表查询和拒绝功能。
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def list_pending_users(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 50,
) -> list[User]:
    """查询所有 Pending 状态的用户。"""
    result = await db.execute(
        select(User).where(User.role_code == "pending").offset(offset).limit(limit)
    )
    return list(result.scalars().all())


async def _get_pending_user(user_id: str, db: AsyncSession) -> Optional[User]:
    """查询指定 ID 的 Pending 用户。"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.role_code == "pending")
    )
    return result.scalar_one_or_none()


async def reject_user(user_id: str, db: AsyncSession) -> bool:
    """拒绝注册：删除 Pending 用户。"""
    user = await _get_pending_user(user_id, db)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
