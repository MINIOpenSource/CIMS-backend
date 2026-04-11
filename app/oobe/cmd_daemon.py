"""daemon 子命令处理器。

以前台进程模式运行所有 CIMS 服务，供 systemd 直接管理进程生命周期。
替代旧的 `cims serve` 命令。
"""

import asyncio


def handle_daemon() -> None:
    """处理 `cims daemon` 子命令。

    前台运行所有服务（Client / Management / Admin / gRPC），
    适合由 systemd 或终端直接管理。
    """

    from app.core.config import validate_config

    validate_config()

    from app.core.logging import setup_logging

    setup_logging()

    from app.main import _start_servers

    asyncio.run(_start_servers())
