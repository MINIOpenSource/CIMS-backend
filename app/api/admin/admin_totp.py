"""超管 2FA 管理路由。

管理员对指定用户执行 enable/disable/verify/reset TOTP。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.models.session import get_db
from app.models.user import User
from app.services.crypto.totp import generate_totp_secret

router = APIRouter()
_sa = require_role(100)


@router.post("/{user_id}/2fa/enable")
async def admin_enable_2fa(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """为指定用户启用 TOTP。"""
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")
    secret = generate_totp_secret()
    user.totp_secret = secret
    user.totp_enabled = True
    await db.commit()
    return {"secret": secret}
