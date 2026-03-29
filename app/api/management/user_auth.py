"""用户登录认证端点。

验证凭据后签发会话令牌，支持 2FA 流程。
"""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user_out import UserLoginRequest
from app.models.session import get_db
from app.services.user.login import login_user

router = APIRouter()


@router.post("/auth")
async def user_login(
    payload: UserLoginRequest = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """用户登录，返回令牌或进入 2FA 流程。"""
    try:
        token, user, needs_2fa = await login_user(payload.email, payload.password, db)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    if needs_2fa:
        from app.api.admin.totp_temp import create_2fa_temp_token

        temp = await create_2fa_temp_token(user.id)
        return {"requires_2fa": True, "temp_token": temp}
    return {"token": token}
