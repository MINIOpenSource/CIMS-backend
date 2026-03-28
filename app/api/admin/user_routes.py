"""超管用户管理路由。

提供用户列表查询、搜索、创建和详情查看端点。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user_out import UserOut, UserUpdateRequest
from app.core.auth.dependencies import require_role
from app.models.session import get_db
from app.services.user.manager import list_users, get_user_by_id, update_user
from app.services.user.register import register_user
from .user_helpers import _to_out

router = APIRouter()
_sa = require_role(100)


@router.get("/list", response_model=list[UserOut])
async def list_all_users(
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """分页查询所有用户。"""
    users, _ = await list_users(db, offset=offset, limit=limit)
    return [_to_out(u) for u in users]


@router.get("/search", response_model=list[UserOut])
async def search_users(
    q: str = "",
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """按关键字搜索用户。"""
    users, _ = await list_users(db, search=q)
    return [_to_out(u) for u in users]
