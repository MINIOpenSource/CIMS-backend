"""客户端 API 应用定义。

挂载面向终端设备的资源下载、Manifest 获取以及引导配置接口。
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.client.router import router as client_router
from app.api.client.token_get import router as token_get_router
from app.api.management_config.routes import router as mc_router
from app.core.auth.http_middleware import TenantMiddleware
from app.core.logging import RequestLoggingMiddleware, PORT_TAG_CLIENT
from app.core.security.middleware import CCProtectMiddleware
from app.core.security.errors import apply_app_safeguards
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
client_app.add_middleware(CCProtectMiddleware)

apply_app_safeguards(client_app)

# 挂载业务路由
client_app.include_router(client_router, prefix="/api", tags=["Client"])
client_app.include_router(mc_router, prefix="/api", tags=["Guide"])
client_app.include_router(token_get_router, tags=["TokenGet"])


@client_app.get("/")
async def root():
    """终端 API 状态检测。"""
    return {"message": "CIMS Backend is running"}
