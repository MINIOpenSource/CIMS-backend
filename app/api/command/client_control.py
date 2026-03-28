"""客户端远程控制。

通过 gRPC 长连接向客户端下发实时控制指令。
按 NewAPI.md: POST /{client_id}/command/restart, POST /{client_id}/command/update-data
"""

from fastapi import APIRouter, Request
from app.core.tenant.context import get_tenant_id
from app.api.schemas.base import StatusResponse
from app.grpc.api.Protobuf.Server import ClientCommandDeliverScRsp_pb2
from app.grpc.api.Protobuf.Enum import Retcode_pb2, CommandTypes_pb2

router = APIRouter()


async def _push_cmd(request: Request, uid: str, cmd_type: int) -> StatusResponse:
    """内部辅助：发送简单的无负载 gRPC 指令。"""
    servicer = getattr(request.app.state, "command_servicer", None)
    if not servicer:
        return StatusResponse(status="error", message="gRPC 服务不可用")

    cmd = ClientCommandDeliverScRsp_pb2.ClientCommandDeliverScRsp(
        RetCode=Retcode_pb2.Success, Type=cmd_type
    )
    await servicer.send_command(get_tenant_id(), uid, cmd)
    return StatusResponse(status="success", message="指令已下发")


@router.post("/{client_id}/command/restart", response_model=StatusResponse)
async def restart_app(client_id: str, request: Request):
    """要求指定客户端重新启动应用。"""
    return await _push_cmd(request, client_id, CommandTypes_pb2.RestartApp)


@router.post("/{client_id}/command/update-data", response_model=StatusResponse)
async def force_sync(client_id: str, request: Request):
    """触发客户端立即拉取并刷新最新配置数据。"""
    return await _push_cmd(request, client_id, CommandTypes_pb2.DataUpdated)
