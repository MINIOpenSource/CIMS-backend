"""CIMS 后端服务主入口。

负责并发启动面向终端的 Client API、面向用户的 Management API
和面向超管的 Admin API。gRPC 由 Client API 的 lifespan 管理。
通过 `cims daemon` 运行，或直接作为模块执行。
"""

import asyncio
import logging
import os
from pathlib import Path

import uvicorn

from app.core.config import CLIENT_PORT, MANAGEMENT_PORT, ADMIN_PORT
from app.oobe.detector import is_initialized

logger = logging.getLogger(__name__)

# PID 文件路径
_PID_FILE = Path(".cims") / "cims.pid"


def _write_pid() -> None:
    """将当前进程 PID 写入文件。"""
    _PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    logger.info("PID %d 已写入 %s", os.getpid(), _PID_FILE)


def _remove_pid() -> None:
    """删除 PID 文件。"""
    try:
        _PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def read_pid() -> int | None:
    """读取 PID 文件中的进程 ID。

    Returns:
        进程 ID 整数，文件不存在或内容无效时返回 None。
    """
    if not _PID_FILE.exists():
        return None
    try:
        return int(_PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


async def _start_servers():
    """并发运行三个独立的 uvicorn 实例（前台模式）。

    - 写入 PID 文件
    - 禁用 uvicorn 默认日志（由统一日志系统接管）
    - 注册信号处理器用于优雅停机
    """
    _write_pid()

    # uvicorn 配置：禁用默认日志，由 app.core.logging 统一接管
    uv_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {},
        "loggers": {},
    }

    if is_initialized():
        from app.apps.client_app import client_app
        from app.apps.management_app import management_app
        from app.apps.admin_app import admin_app

        c_app, m_app, a_app = client_app, management_app, admin_app
    else:
        from app.core.security.oobe_guard import generate_oobe_codes
        from app.apps.oobe_apps import oobe_stub_app, oobe_admin_app

        generate_oobe_codes()
        c_app, m_app, a_app = oobe_stub_app, oobe_stub_app, oobe_admin_app

    c_cfg = uvicorn.Config(
        c_app,
        host="0.0.0.0",
        port=CLIENT_PORT,
        log_config=uv_log_config,
        access_log=False,
    )
    m_cfg = uvicorn.Config(
        m_app,
        host="0.0.0.0",
        port=MANAGEMENT_PORT,
        log_config=uv_log_config,
        access_log=False,
    )
    a_cfg = uvicorn.Config(
        a_app,
        host="0.0.0.0",
        port=ADMIN_PORT,
        log_config=uv_log_config,
        access_log=False,
    )

    logger.info(
        "启动服务 — Client:%d  Management:%d  Admin:%d  (PID: %d)",
        CLIENT_PORT,
        MANAGEMENT_PORT,
        ADMIN_PORT,
        os.getpid(),
    )

    servers = [
        uvicorn.Server(c_cfg),
        uvicorn.Server(m_cfg),
        uvicorn.Server(a_cfg),
    ]

    try:
        await asyncio.gather(*(s.serve() for s in servers))
    finally:
        _remove_pid()
        logger.info("所有服务已停止，PID 文件已清理")


def main():
    """主程序（统一 CLI）入口。"""
    from app.oobe import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
