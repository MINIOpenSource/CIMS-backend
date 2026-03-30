"""Management API 聚合路由。

按 NewAPI.md 定义的路由树组装所有子路由模块。
"""

from fastapi import APIRouter

from .token_refresh import router as ref_r
from .token_verify import router as ver_r
from .token_deactivate import router as deact_r
from .user_apply import router as apply_r
from .user_auth import router as auth_r
from .user_availability_mail import router as avail_mail_r
from .user_availability_username import router as avail_uname_r
from .user_info import router as info_r
from .user_totp import router as totp_r
from .user_info_email import router as email_r
from .user_info_username import router as uname_r
from .user_password import router as pwd_r

router = APIRouter()

# /token/*
router.include_router(ref_r, prefix="/token", tags=["Token"])
router.include_router(ver_r, prefix="/token", tags=["Token"])
router.include_router(deact_r, prefix="/token", tags=["Token"])

# /user/*
router.include_router(apply_r, prefix="/user", tags=["User"])
router.include_router(auth_r, prefix="/user", tags=["User"])
router.include_router(info_r, prefix="/user", tags=["User"])
router.include_router(totp_r, prefix="/user/2fa/totp", tags=["2FA"])

# /user/availability/*（无需认证）
router.include_router(avail_mail_r, prefix="/user/availability", tags=["Availability"])
router.include_router(avail_uname_r, prefix="/user/availability", tags=["Availability"])

# /user/info/*
router.include_router(email_r, prefix="/user/info", tags=["UserInfo"])
router.include_router(uname_r, prefix="/user/info", tags=["UserInfo"])
router.include_router(pwd_r, prefix="/user/info/password", tags=["UserInfo"])
