"""超管用户详情路由。

提供查看、修改、删除和重命名用户。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user_out import UserOut, UserUpdateRequest
from app.core.auth.dependencies import require_role
from app.models.session import get_db
from app.services.user.manager import get_user_by_id, update_user
from .user_helpers import _to_out

router = APIRouter()
_sa = require_role(100)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """获取用户信息。"""
    user = await get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _to_out(user)


@router.post("/{user_id}", response_model=UserOut)
async def update_user_info(
    user_id: str,
    body: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """修改用户信息。"""
    updated = await update_user(user_id, db, **body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _to_out(updated)
