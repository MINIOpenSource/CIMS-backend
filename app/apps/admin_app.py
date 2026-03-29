"""超级管理员 API 应用定义。

仅供超级管理员使用的平台级管理接口，
按 NewAPI.md 结构：/user/*、/account、/settings、/bulk。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.admin.router import router as admin_router
from app.core.auth.admin_middleware import AdminAuthMiddleware
from app.core.logging import RequestLoggingMiddleware, PORT_TAG_ADMIN

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

# 平台级管理路由
admin_app.include_router(admin_router)


@admin_app.exception_handler(Exception)
async def _global_exc(request: Request, exc: Exception):
    """全局异常拦截，避免泄露内部信息。"""
    logger.exception("未处理异常: %s %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


@admin_app.get("/")
async def root():  # pragma: no cover
    """超管 API 状态检测。"""
    return {"message": "CIMS 超管 API 运行中"}
