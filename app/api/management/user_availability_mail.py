"""邮箱可用性检查端点。

供注册页前端实时校验邮箱是否已被占用，无需身份认证。
"""

from fastapi import APIRouter, Query
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.models.session import get_db
from app.models.user import User

router = APIRouter()


@router.get("/mail")
async def check_mail_availability(
    value: EmailStr = Query(..., description="待检查的邮箱地址"),
    db: AsyncSession = Depends(get_db),
):
    """检查邮箱是否可用（未被注册）。"""
    result = await db.execute(select(User.id).where(User.email == value))
    exists = result.scalar_one_or_none() is not None
    return {"available": not exists}
