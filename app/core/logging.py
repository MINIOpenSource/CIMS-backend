"""CIMS 统一日志系统。

接管 FastAPI / uvicorn / gRPC 全部日志流，
为四个接口（Client / Management / Admin / gRPC）提供统一的结构化日志输出。

日志同时写入：
  - 标准输出（供 systemd / journalctl 捕获）
  - 文件 .cims/logs/cims-YYYY-MM-DD.log（按日自动轮转）

每条日志格式：
  2026-03-25 08:01:23.456 | INFO  | CLIENT  | app.api.client | 消息内容
"""

import logging
import sys
import time
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.client_ip import get_client_ip_from_request

# ---- 常量 ----
_LOG_DIR = Path(".cims") / "logs"
_LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(levelname)-5s | %(port_tag)-7s | %(name)-30s | %(message)s"
_LOG_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# 端口标签映射
PORT_TAG_CLIENT = "CLIENT"
PORT_TAG_MGMT = "MGMT"
PORT_TAG_ADMIN = "ADMIN"
PORT_TAG_GRPC = "GRPC"
PORT_TAG_SYSTEM = "SYSTEM"


class _PortTagFilter(logging.Filter):
    """为日志记录注入 port_tag 字段（默认 SYSTEM）。"""

    def __init__(self, tag: str = PORT_TAG_SYSTEM):
        """初始化端口标签过滤器。

        Args:
            tag: 端口标签，如 CLIENT / MGMT / ADMIN / GRPC / SYSTEM。
        """
        super().__init__()
        self.tag = tag

    def filter(self, record: logging.LogRecord) -> bool:
        """为日志记录添加 port_tag 属性。"""
        if not hasattr(record, "port_tag"):
            record.port_tag = self.tag  # type: ignore[attr-defined]
        return True


class _ColorFormatter(logging.Formatter):
    """终端彩色日志格式化器。

    各端口标签使用不同 ANSI 颜色以便在终端区分：
      CLIENT  → 青色
      MGMT    → 黄色
      ADMIN   → 品红色
      GRPC    → 绿色
      SYSTEM  → 白色
    """

    _COLORS = {
        PORT_TAG_CLIENT: "\033[36m",  # 青色
        PORT_TAG_MGMT: "\033[33m",  # 黄色
        PORT_TAG_ADMIN: "\033[35m",  # 品红色
        PORT_TAG_GRPC: "\033[32m",  # 绿色
        PORT_TAG_SYSTEM: "\033[37m",  # 白色
    }
    _LEVEL_COLORS = {
        "DEBUG": "\033[90m",  # 灰色
        "INFO": "\033[97m",  # 亮白
        "WARNING": "\033[93m",  # 亮黄
        "ERROR": "\033[91m",  # 亮红
        "CRITICAL": "\033[41m",  # 红底
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        """格式化日志记录，添加 ANSI 颜色。"""
        tag = getattr(record, "port_tag", PORT_TAG_SYSTEM)
        tag_color = self._COLORS.get(tag, self._RESET)
        level_color = self._LEVEL_COLORS.get(record.levelname, self._RESET)

        # 着色端口标签和级别
        original_tag = record.port_tag  # type: ignore[attr-defined]
        original_levelname = record.levelname
        record.port_tag = f"{tag_color}{tag}{self._RESET}"  # type: ignore[attr-defined]
        record.levelname = f"{level_color}{record.levelname}{self._RESET}"

        result = super().format(record)

        # 还原（避免影响文件 handler）
        record.port_tag = original_tag  # type: ignore[attr-defined]
        record.levelname = original_levelname
        return result


def setup_logging(*, level: int = logging.INFO) -> None:
    """初始化全局日志系统。

    - 配置 root logger
    - 抑制 uvicorn 默认日志配置
    - 同时输出到终端（带颜色）和文件（纯文本）

    Args:
        level: 日志级别，默认 INFO。
    """
    # 确保日志目录存在
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    # root logger
    root = logging.getLogger()
    root.setLevel(level)
    # 清除已有 handler 避免重复
    root.handlers.clear()

    # ---- 终端 handler（带颜色） ----
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_fmt = _ColorFormatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT)
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(_PortTagFilter(PORT_TAG_SYSTEM))
    root.addHandler(console_handler)

    # ---- 文件 handler（按日轮转） ----
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = _LOG_DIR / f"cims-{today}.log"
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        utc=True,
    )
    file_handler.setLevel(level)
    file_fmt = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT)
    file_handler.setFormatter(file_fmt)
    file_handler.addFilter(_PortTagFilter(PORT_TAG_SYSTEM))
    root.addHandler(file_handler)

    # ---- 抑制 uvicorn 默认日志 ----
    for uv_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(uv_name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True

    # ---- 降低第三方库日志级别 ----
    for noisy in ("asyncio", "aiohttp", "sqlalchemy.engine", "grpc"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root.info(
        "日志系统已初始化 — 级别: %s  输出: 终端 + %s",
        logging.getLevelName(level),
        log_file,
    )


def get_port_logger(tag: str) -> logging.Logger:
    """获取带端口标签的 logger。

    Args:
        tag: 端口标签，如 CLIENT / MGMT / ADMIN / GRPC。

    Returns:
        已配置端口标签过滤器的 Logger 实例。
    """
    name = f"cims.{tag.lower()}"
    logger = logging.getLogger(name)
    # 仅添加一次过滤器
    if not any(isinstance(f, _PortTagFilter) for f in logger.filters):
        logger.addFilter(_PortTagFilter(tag))
    return logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP 请求详细日志中间件。

    记录每个请求的：
      - 客户端 IP
      - 请求方法和路径
      - 查询参数
      - 响应状态码
      - 处理耗时（毫秒）

    为各 FastAPI app 实例分别实例化，传入端口标签以区分日志来源。
    """

    def __init__(self, app, port_tag: str = PORT_TAG_SYSTEM):
        """初始化请求日志中间件。

        Args:
            app: ASGI 应用实例。
            port_tag: 端口标签字符串。
        """
        super().__init__(app)
        self.port_tag = port_tag
        self.logger = get_port_logger(port_tag)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """拦截请求，记录详细日志。"""
        start = time.perf_counter()
        client_ip = get_client_ip_from_request(request)
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""

        # 记录请求开始
        self.logger.debug(
            "→ %s %s%s  来自 %s",
            method,
            path,
            f"?{query}" if query else "",
            client_ip,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            self.logger.error(
                "✗ %s %s  来自 %s  耗时 %.1fms  异常: %s",
                method,
                path,
                client_ip,
                elapsed,
                exc,
            )
            raise

        elapsed = (time.perf_counter() - start) * 1000
        status = response.status_code

        # 根据状态码选择日志级别
        if status >= 500:
            log_fn = self.logger.error
        elif status >= 400:
            log_fn = self.logger.warning
        else:
            log_fn = self.logger.info

        log_fn(
            "%s %s %s  来自 %s  耗时 %.1fms",
            status,
            method,
            path,
            client_ip,
            elapsed,
        )

        return response
