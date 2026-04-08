"""命令分发双向流。

维护客户端长连接并推送管理指令，强制验证 session 与 cuid 匹配。
"""

import asyncio
import grpc
import logging
from typing import Dict
from app.grpc.api.Protobuf.Service import ClientCommandDeliver_pb2_grpc
from app.core.client_ip import get_client_ip_from_grpc
from .helpers import get_metadata_dict, get_tenant_id_safe

logger = logging.getLogger(__name__)

# 每个客户端的指令队列上限，防止资源耗尽
_QUEUE_MAXSIZE = 256


class ClientCommandDeliverServicer(
    ClientCommandDeliver_pb2_grpc.ClientCommandDeliverServicer
):
    """处理指令监听与心跳。"""

    def __init__(self, session_manager):
        self._sm = session_manager
        self.client_queues: Dict[str, asyncio.Queue] = {}

    async def ListenCommand(self, request_iterator, context):
        """双向流：验证 session 后建立连接、心跳、下发指令。"""
        md = get_metadata_dict(context)
        sid = md.get("session", "")

        # 强制校验 session 并提取绑定的 cuid
        real_cuid = await self._sm.validate_session(sid)
        if not real_cuid:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "会话无效")
            return

        tid = await self._sm.get_session_tenant(sid) or get_tenant_id_safe()

        # 注册在线状态与有界消息队列
        client_ip = get_client_ip_from_grpc(context)
        await self._sm.set_client_online(
            tid, real_cuid, ip=client_ip
        )
        q_key = f"{tid}:{real_cuid}"
        queue = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)
        self.client_queues[q_key] = queue

        logger.info("[%s] gRPC 流已建立: 状态=Online, tid=%s, cuid=%s", client_ip, tid, real_cuid)

        try:
            from .command_utils import run_command_loop

            async for resp in run_command_loop(
                self, request_iterator, queue, tid, real_cuid
            ):
                yield resp
        finally:
            self.client_queues.pop(q_key, None)
            await self._sm.set_client_offline(tid, real_cuid)
            logger.info("[%s] gRPC 流已断开: 状态=Offline, tid=%s, cuid=%s", client_ip, tid, real_cuid)

    async def send_command(self, tid, cuid, cmd):
        """API 向特定客户端注入指令的公共方法。"""
        key = f"{tid}:{cuid}"
        if key in self.client_queues:
            await self.client_queues[key].put(cmd)
