"""全局应用生命周期管理 — 启动阶段。

控制数据库初始化、Redis 连接池分配以及 gRPC 服务器启动。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import (
    validate_config,
    CLIENT_PORT,
    MANAGEMENT_PORT,
    ADMIN_PORT,
    GRPC_PORT,
)
from app.core.redis.pool import init_redis
from app.models.database import init_db
from app.grpc.server.bootstrap import serve_grpc
from app.core.logging import get_port_logger, PORT_TAG_GRPC
from app.apps.lifespan_shutdown import _shutdown

logger = logging.getLogger(__name__)
grpc_logger = get_port_logger(PORT_TAG_GRPC)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """FastAPI 生命周期管理。"""
    validate_config()
    await _startup(app)
    yield
    await _shutdown(app)


async def _startup(app: FastAPI):
    """启动所有后端服务。"""
    logger.info("正在初始化数据库连接...")
    await init_db()
    logger.info("正在初始化 Redis 连接池...")
    await init_redis()
    grpc_logger.info("正在启动 gRPC (%d)...", GRPC_PORT)
    grpc_s, cmd_s, sess_m = await serve_grpc()
    app.state.grpc_server = grpc_s
    app.state.command_servicer = cmd_s
    app.state.session_manager = sess_m
    logger.info(
        "就绪 — C:%d M:%d A:%d G:%d",
        CLIENT_PORT,
        MANAGEMENT_PORT,
        ADMIN_PORT,
        GRPC_PORT,
    )
