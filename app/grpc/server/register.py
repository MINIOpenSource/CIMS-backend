"""客户端注册服务逻辑。

处理终端设备注册入网及注销请求，
支持可选的配对码审批流程。
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import select

from app.models.database import AsyncSessionLocal, ClientRecord
from app.models.system_config import SystemConfig
from app.grpc.api.Protobuf.Client import ClientRegisterCsReq_pb2
from app.grpc.api.Protobuf.Server import ClientRegisterScRsp_pb2
from app.grpc.api.Protobuf.Enum import Retcode_pb2
from app.grpc.api.Protobuf.Service import ClientRegister_pb2_grpc
from app.services.pairing_utils import (
    create_pairing_request,
    check_approved,
)
from .helpers import get_tenant_id_safe
from .unregister import handle_unregister

logger = logging.getLogger(__name__)

_PAIRING_KEY = "pairing_enabled"


def _extract_peer_ip(context) -> str:
    """从 gRPC 上下文中提取客户端 IP。"""
    peer = context.peer()
    if peer and ":" in peer:
        parts = peer.split(":")
        if len(parts) >= 2:
            return parts[1]
    return "unknown"


async def _is_pairing_enabled(db) -> bool:
    """检查配对码功能是否已启用。"""
    stmt = select(SystemConfig).where(SystemConfig.key == _PAIRING_KEY)
    cfg = (await db.execute(stmt)).scalar_one_or_none()
    return cfg is not None and cfg.value == "true"


class ClientRegisterServicer(ClientRegister_pb2_grpc.ClientRegisterServicer):
    """管理终端注册生命周期（含配对码支持）。"""

    def __init__(self, session_manager):
        self._sm = session_manager

    async def Register(self, request: ClientRegisterCsReq_pb2, context):
        """记录新客户端信息或更新现有设备的 MAC 地址。"""
        cuid = request.ClientUid
        tid = get_tenant_id_safe()
        peer_ip = _extract_peer_ip(context)

        async with AsyncSessionLocal() as db:
            from app.core.tenant.context import set_search_path

            await set_search_path(db)

            # 配对码检查
            if await _is_pairing_enabled(db):
                already_approved = await check_approved(cuid, tid)
                if not already_approved:
                    code = await create_pairing_request(
                        tenant_id=tid,
                        client_uid=cuid,
                        client_id=request.ClientId,
                        client_mac=request.ClientMac,
                        client_ip=peer_ip,
                    )
                    logger.info(
                        "配对码拦截: uid=%s code=%s ip=%s",
                        cuid,
                        code,
                        peer_ip,
                    )
                    return ClientRegisterScRsp_pb2.ClientRegisterScRsp(
                        Retcode=Retcode_pb2.PairingRequired,
                        Message=(
                            f"需要配对码加入组织。"
                            f"您的配对码：{code}，"
                            f"请联系管理员审批后重新连接。"
                        ),
                    )

            # 正常注册流程
            stmt = select(ClientRecord).where(ClientRecord.uid == cuid)
            record = (await db.execute(stmt)).scalar_one_or_none() or ClientRecord(
                uid=cuid, registered_at=datetime.now(timezone.utc)
            )
            record.client_id = request.ClientId
            record.mac = request.ClientMac
            db.add(record)
            await db.commit()

        logger.info("设备注册成功: uid=%s ip=%s", cuid, peer_ip)
        return ClientRegisterScRsp_pb2.ClientRegisterScRsp(
            Retcode=Retcode_pb2.Registered,
            ServerPublicKey=self._sm.public_key_armor,
        )

    async def UnRegister(self, request, context):
        """验证 session 后注销设备记录（委托至 unregister 模块）。"""
        return await handle_unregister(self._sm, request, context)
