"""用户名可用性检查端点。

供注册页前端实时校验用户名是否可用，无需身份认证。
校验流程：格式合法性 → 保留名检查 → 唯一性查询。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import get_db
from app.models.user import User
from app.services.user.name_validator import (
    is_name_reserved,
    validate_username_format,
)

router = APIRouter()


@router.get("/username")
async def check_username_availability(
    value: str = Query(..., min_length=3, max_length=64, description="待检查的用户名"),
    db: AsyncSession = Depends(get_db),
):
    """检查用户名是否可用。

    依次校验格式、保留名和唯一性，返回结果与不可用原因。
    """
    if not validate_username_format(value):
        return {"available": False, "reason": "用户名格式不合法"}
    if await is_name_reserved(value, db):
        return {"available": False, "reason": "该名称为系统保留名"}
    result = await db.execute(select(User.id).where(User.username == value))
    if result.scalar_one_or_none() is not None:
        return {"available": False, "reason": "该用户名已被占用"}
    return {"available": True}
