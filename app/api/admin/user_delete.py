"""超管用户删除和重命名路由。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.models.session import get_db
from app.models.user import User

router = APIRouter()
_sa = require_role(100)


class RenameRequest(BaseModel):
    """重命名请求体。"""

    name: str = Field(..., min_length=1, max_length=64)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """删除用户。"""
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user)
    await db.commit()
    return {"message": "用户已删除"}


@router.post("/{user_id}/rename")
async def rename_user(
    user_id: str,
    body: RenameRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """重命名用户。"""
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.username = body.name
    await db.commit()
    return {"message": "已重命名"}
