"""客户端 API 应用定义。

挂载面向终端设备的资源下载、Manifest 获取以及引导配置接口。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.client.router import router as client_router
from app.api.client.token_get import router as token_get_router
from app.api.management_config.routes import router as mc_router
from app.core.auth.http_middleware import TenantMiddleware
from app.core.logging import RequestLoggingMiddleware, PORT_TAG_CLIENT
from .lifespan import app_lifespan

logger = logging.getLogger(__name__)

# 客户端 App 实例（绑定全局生命周期）
client_app = FastAPI(title="CIMS 客户端 API", version="0.2.0", lifespan=app_lifespan)

# CORS 中间件（允许前端跨域获取资源）
client_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client_app.add_middleware(TenantMiddleware)
client_app.add_middleware(RequestLoggingMiddleware, port_tag=PORT_TAG_CLIENT)

# 挂载业务路由
client_app.include_router(client_router, prefix="/api", tags=["Client"])
client_app.include_router(mc_router, prefix="/api", tags=["Guide"])
client_app.include_router(token_get_router, tags=["TokenGet"])


@client_app.exception_handler(Exception)
async def _global_exc(request: Request, exc: Exception):
    """全局异常拦截，避免泄露内部信息。"""
    logger.exception("未处理异常: %s %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


@client_app.get("/")
async def root():
    """终端 API 状态检测。"""
    return {"message": "CIMS Backend is running"}
