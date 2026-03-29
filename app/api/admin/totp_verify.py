"""2FA 登录验证端点。"""

from fastapi import HTTPException
from sqlalchemy import select

from . import totp_routes as mod
from app.models.user import User
from app.services.crypto.totp import verify_totp
from app.services.crypto.token_factory import create_session_token
from app.api.schemas.totp import TotpVerifyRequest
from .totp_temp import _pop_temp_token


@mod.router.post("/verify")
async def verify_2fa_login(body: TotpVerifyRequest):
    """提交 TOTP 码完成登录。"""
    uid = await _pop_temp_token(body.temp_token)
    from app.models.engine import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == uid))).scalar_one()
    if not verify_totp(user.totp_secret, body.code):
        raise HTTPException(401, "TOTP 码无效")
    token = await create_session_token(uid)
    return {"token": token, "user_id": uid}
