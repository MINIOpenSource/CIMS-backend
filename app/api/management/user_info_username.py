"""用户名修改路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.models.session import get_db
from app.models.user import User
from app.services.user.name_validator import validate_username_format
from app.api.schemas.profile import UsernameUpdate

router = APIRouter()


@router.post("/username")
async def change_username(
    body: UsernameUpdate,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    """修改当前用户名。"""
    if not validate_username_format(body.username):
        raise HTTPException(400, "用户名格式不合法")
    # 唯一性校验
    dup = await db.execute(
        select(User).where(User.username == body.username, User.id != uid)
    )
    if dup.scalar_one_or_none():
        raise HTTPException(400, "该用户名已被占用")
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.username = body.username
    await db.commit()
    return {"message": "用户名已更新"}
