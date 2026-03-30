"""账户 Slug 可用性检查端点。

供已登录用户创建账户时校验 Slug 是否可用，需身份认证。
校验流程：格式合法性 → 保留名检查 → 唯一性查询。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.session import get_db
from app.services.user.name_validator import (
    is_name_reserved,
    validate_slug_format,
)

router = APIRouter()


@router.get("/slug")
async def check_slug_availability(
    value: str = Query(..., min_length=3, max_length=64, description="待检查的 Slug"),
    db: AsyncSession = Depends(get_db),
):
    """检查账户 Slug 是否可用。

    依次校验格式、保留名和唯一性，返回结果与不可用原因。
    """
    if not validate_slug_format(value):
        return {"available": False, "reason": "Slug 格式不合法"}
    if await is_name_reserved(value, db):
        return {"available": False, "reason": "该名称为系统保留名"}
    result = await db.execute(select(Account.id).where(Account.slug == value))
    if result.scalar_one_or_none() is not None:
        return {"available": False, "reason": "该 Slug 已被占用"}
    return {"available": True}
