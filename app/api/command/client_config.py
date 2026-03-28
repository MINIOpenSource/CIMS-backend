"""远程配置查询路由。

按 NewAPI.md: GET /{client_id}/command/get-config
"""

import uuid
from fastapi import APIRouter, Request
from app.core.tenant.context import get_tenant_id
from app.grpc.api.Protobuf.Server import ClientCommandDeliverScRsp_pb2
from app.grpc.api.Protobuf.Command import GetClientConfig_pb2
from app.grpc.api.Protobuf.Enum import Retcode_pb2, CommandTypes_pb2

router = APIRouter()


@router.get("/{client_id}/command/get-config")
async def fetch_runtime_config(client_id: str, config_type: int, request: Request):
    """请求终端上报其当前运行的配置快照。"""
    servicer = getattr(request.app.state, "command_servicer", None)
    if not servicer:
        return {"status": "error", "message": "通讯通道关闭"}

    req_id = str(uuid.uuid4())
    config_req = GetClientConfig_pb2.GetClientConfig(
        RequestGuid=req_id, ConfigType=config_type
    )

    cmd = ClientCommandDeliverScRsp_pb2.ClientCommandDeliverScRsp(
        RetCode=Retcode_pb2.Success,
        Type=CommandTypes_pb2.GetClientConfig,
        Payload=config_req.SerializeToString(),
    )

    await servicer.send_command(get_tenant_id(), client_id, cmd)
    return {
        "status": "success",
        "message": f"请求已下发，ID: {req_id}",
        "request_guid": req_id,
    }
