"""命令流辅助工具。

封装双向流异步读写循环，含心跳响应、Ping 速率限制与空闲超时。
"""

import asyncio
import time
from app.grpc.api.Protobuf.Enum import Retcode_pb2, CommandTypes_pb2
from app.grpc.api.Protobuf.Server import ClientCommandDeliverScRsp_pb2
import logging
from .stream_timeout import get_with_timeout

logger = logging.getLogger(__name__)

# Ping 最小间隔（秒），防止客户端洪泛
_MIN_PING_INTERVAL = 1.0


async def run_command_loop(servicer, request_iterator, queue, tid, cuid):
    """运行长连接读写工作流，含速率限制和空闲超时。"""
    last_ping = 0.0

    async def read_task():
        nonlocal last_ping
        async for req in request_iterator:
            if req.Type == CommandTypes_pb2.Ping:
                logger.debug("指令流状态: 收到心跳 Ping (tid=%s, cuid=%s)", tid, cuid)
                now = time.monotonic()
                if now - last_ping < _MIN_PING_INTERVAL:
                    continue  # 速率限制：丢弃过频心跳
                last_ping = now
                await servicer._sm.update_heartbeat(tid, cuid)
                pong = ClientCommandDeliverScRsp_pb2.ClientCommandDeliverScRsp(
                    RetCode=Retcode_pb2.Success, Type=CommandTypes_pb2.Pong
                )
                await queue.put(pong)
            else:
                logger.info(
                    "指令流上行: 收到客户端指令 type=%s (tid=%s, cuid=%s)",
                    req.Type,
                    tid,
                    cuid,
                )

    task = asyncio.create_task(read_task())
    try:
        while True:
            # 使用带超时的读取，防止 TCP 半开连接永久阻塞
            msg = await get_with_timeout(queue)
            if getattr(msg, "Type", None) == CommandTypes_pb2.Pong:
                logger.debug("指令流下发: 返回心跳 Pong (tid=%s, cuid=%s)", tid, cuid)
            else:
                cmd_type = getattr(msg, "Type", "Unknown")
                logger.info(
                    "指令流下发: 推送指令 type=%s (tid=%s, cuid=%s)",
                    cmd_type,
                    tid,
                    cuid,
                )
            yield msg
            queue.task_done()
    except (asyncio.CancelledError, asyncio.TimeoutError) as e:
        logger.warning("gRPC 流异常结束: type=%s, 错误=%s", type(e).__name__, str(e))
        task.cancel()
