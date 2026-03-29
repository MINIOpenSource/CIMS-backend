"""用户资料变更路由。

邮箱修改。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.models.session import get_db
from app.models.user import User
from app.api.schemas.profile import EmailUpdate

router = APIRouter()


@router.post("/email")
async def change_email(
    body: EmailUpdate,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    """修改当前用户邮箱。"""
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.email = body.email
    await db.commit()
    return {"message": "邮箱已更新"}
