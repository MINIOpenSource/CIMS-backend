"""超级管理员 API 应用定义。

仅供超级管理员使用的平台级管理接口，
按 NewAPI.md 结构：/user/*、/account、/settings、/bulk。
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin.router import router as admin_router
from app.core.auth.admin_middleware import AdminAuthMiddleware
from app.core.logging import RequestLoggingMiddleware, PORT_TAG_ADMIN
from app.core.security.middleware import CCProtectMiddleware
from app.core.security.errors import apply_app_safeguards

logger = logging.getLogger(__name__)

admin_app = FastAPI(
    title="CIMS 超管 API",
    version="0.3.0",
    redirect_slashes=False,
)

# CORS 中间件
admin_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 超管认证中间件
admin_app.add_middleware(AdminAuthMiddleware)
admin_app.add_middleware(RequestLoggingMiddleware, port_tag=PORT_TAG_ADMIN)
admin_app.add_middleware(CCProtectMiddleware)

apply_app_safeguards(admin_app)

# 平台级管理路由
admin_app.include_router(admin_router)


@admin_app.get("/")
async def root():  # pragma: no cover
    """超管 API 状态检测。"""
    return {"message": "CIMS 超管 API 运行中"}
