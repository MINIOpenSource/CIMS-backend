"""Management API 应用定义。

面向普通用户的管理接口，提供认证、账户操作和资源管理。
使用 AccountContextMiddleware 通过路径参数确定账户上下文。
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.management.router import router as mgr_router
from app.api.management.account_router import router as acct_router
from app.core.auth.admin_middleware import AdminAuthMiddleware
from app.core.auth.account_middleware import AccountContextMiddleware
from app.core.logging import RequestLoggingMiddleware, PORT_TAG_MGMT
from app.core.security.middleware import CCProtectMiddleware
from app.core.security.errors import apply_app_safeguards

logger = logging.getLogger(__name__)

management_app = FastAPI(
    title="CIMS 管理 API",
    version="0.3.0",
    redirect_slashes=False,
)

# CORS 中间件
management_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 账户上下文中间件（校验 AccountMember 成员资格）
management_app.add_middleware(AccountContextMiddleware, require_membership=True)

# 会话令牌认证中间件
management_app.add_middleware(AdminAuthMiddleware)
management_app.add_middleware(RequestLoggingMiddleware, port_tag=PORT_TAG_MGMT)
management_app.add_middleware(CCProtectMiddleware)

# 应用自定义防线机制
apply_app_safeguards(management_app)

# 挂载路由
management_app.include_router(mgr_router)
management_app.include_router(acct_router)


@management_app.get("/")
async def root():  # pragma: no cover
    """Management API 状态检测。"""
    return {"message": "CIMS Management API 运行中"}
