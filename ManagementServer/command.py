#! -*- coding:utf-8 -*-

#region Presets
#region 导入项目内建库
import Datas
import logger
import BuildInClasses
import QuickValues
#endregion


#region 导入辅助库
import json
#endregion


#region 导入 gRPC 库
from ManagementServer import gRPC
#endregion


#region 导入 Protobuf 构建文件
from Protobuf.Client import (ClientCommandDeliverScReq_pb2, ClientCommandDeliverScReq_pb2_grpc,
                             ClientRegisterCsReq_pb2, ClientRegisterCsReq_pb2_grpc)
from Protobuf.Command import (SendNotification_pb2, SendNotification_pb2_grpc,
                              HeartBeat_pb2, HeartBeat_pb2_grpc)
from Protobuf.Enum import (CommandTypes_pb2, CommandTypes_pb2_grpc,
                           Retcode_pb2, Retcode_pb2_grpc)
from Protobuf.Server import (ClientCommandDeliverScRsp_pb2, ClientCommandDeliverScRsp_pb2_grpc,
                             ClientRegisterScRsp_pb2, ClientRegisterScRsp_pb2_grpc)
from Protobuf.Service import (ClientCommandDeliver_pb2, ClientCommandDeliver_pb2_grpc,
                              ClientRegister_pb2, ClientRegister_pb2_grpc)
#endregion


#region 导入 FastAPI 相关库
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query
from fastapi.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, PlainTextResponse, RedirectResponse, \
    StreamingResponse
from fastapi.exceptions import HTTPException


#endregion


#region 导入配置文件
class _Settings:
    def __init__(self):
        self.conf_name: str = "settings.json"
        self.conf_dict: dict = json.load(open(self.conf_name))

    @property
    async def refresh(self) -> dict:
        self.conf_dict = json.load(open(self.conf_name))
        return self.conf_dict


Settings = _Settings()
#endregion


#region 定义 API 并声明 CORS
command = FastAPI()
command.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
#endregion


#region 内建辅助函数和辅助参量
log = logger.Logger()
RESOURCE_TYPES = ["ClassPlan", "DefaultSettings", "Policy", "Subjects", "TimeLayout"]


#endregion
#endregion


#region Main
#region 客户端配置文件管理相关 API
@command.get("/command/datas/{resource_type}/create", summary="创建配置文件", tags=["配置文件管理"])
async def create(resource_type: str, name: str):
    """创建新的配置文件。"""
    if resource_type in RESOURCE_TYPES:
        log.log(f"尝试创建配置文件：类型={resource_type}, 名称={name}", QuickValues.Log.info)
        try:
            getattr(Datas, resource_type).new(name)
            log.log(f"配置文件 {resource_type}[{name}] 已创建。", QuickValues.Log.info)
            return {"message": f"配置文件 {resource_type}[{name}] 已创建。"}
        except FileExistsError as e:
            log.log(f"创建失败：{e}", QuickValues.Log.warning)
            raise HTTPException(status_code=409, detail=str(e))  # 409 Conflict
        except Exception as e:
            log.log(f"创建配置文件 {resource_type}[{name}] 时发生错误: {e}", QuickValues.Log.error)
            raise HTTPException(status_code=500, detail=f"创建文件时出错: {e}")
    else:
        raise HTTPException(status_code=404, detail=f"无效的资源类型: {resource_type}")


@command.delete("/command/datas/{resource_type}")
@command.delete("/command/datas/{resource_type}/")
@command.delete("/command/datas/{resource_type}/delete")
@command.get("/command/datas/{resource_type}/delete")
async def delete(resource_type: str, name: str) -> None:
    match resource_type:
        case "ClassPlan" | "DefaultSettings" | "Policy" | "Subjects" | "TimeLayout":
            log.log("{resource_type}[{name}] deleted.".format(resource_type=resource_type, name=name),
                    QuickValues.Log.info)
            return getattr(Datas, resource_type).delete(name)
        case _:
            log.log("Unexpected {resource_type}[{name}] not deleted.".format(resource_type=resource_type, name=name),
                    QuickValues.Log.error)
            raise HTTPException(status_code=404)


@command.get("/command/datas/{resource_type}/list")
async def _list(resource_type: str) -> list[str]:
    match resource_type:
        case "ClassPlan" | "DefaultSettings" | "Policy" | "Subjects" | "TimeLayout":
            log.log("List {resource_type}.".format(resource_type=resource_type), QuickValues.Log.info)
            return getattr(Datas, resource_type).refresh()
        case _:
            log.log("Unexpected {resource_type} bot listed..".format(resource_type=resource_type),
                    QuickValues.Log.error)
            raise HTTPException(status_code=404)


@command.get("/command/datas/{resource_type}/rename")
async def rename(resource_type: str, name: str, target: str) -> None:
    match resource_type:
        case "ClassPlan" | "DefaultSettings" | "Policy" | "Subjects" | "TimeLayout":
            log.log(
                "Resource {resource_type}[{name}] renamed into {target}".format(resource_type=resource_type, name=name,
                                                                                target=target), QuickValues.Log.info)
            return getattr(Datas, resource_type).rename(name, target)
        case _:
            log.log("Unexpected {resource_type}[{name}] not renamed into {target}".format(resource_type=resource_type,
                                                                                          name=name, target=target),
                    QuickValues.Log.error)
            raise HTTPException(status_code=404)


@command.put("/command/datas/{resource_type}")
@command.put("/command/datas/{resource_type}/")
@command.put("/command/datas/{resource_type}/write")
@command.post("/command/datas/{resource_type}")
@command.post("/command/datas/{resource_type}/")
@command.post("/command/datas/{resource_type}/write")
@command.get("/command/datas/{resource_type}/write")
async def write(resource_type: str, name: str, request: Request):
    match resource_type:
        case "ClassPlan" | "DefaultSettings" | "Policy" | "Subjects" | "TimeLayout":
            log.log("Resource {resource_type}[{name}] written with {count} bytes.".format(resource_type=resource_type,
                                                                                          name=name, count=len(
                    str(request.body()))), QuickValues.Log.info)
            return getattr(Datas, resource_type).write(name, await request.body())
        case _:
            log.log(
                "Resource {resource_type}[{name}] not written with {count} bytes.".format(resource_type=resource_type,
                                                                                          name=name, count=len(
                        str(request.body()))), QuickValues.Log.error)
            raise HTTPException(status_code=404)


#endregion


#region 服务器配置文件管理相关 API
@command.get("/command/server/settings")
async def setting():
    log.log("Settings gotten.", QuickValues.Log.info)
    return Settings.conf_dict


@command.put("/command/server/settings")
@command.post("/command/server/settings")
async def update_settings(request: Request):
    log.log("Settings changed.", QuickValues.Log.critical)
    with open(Settings.conf_name, "w") as f:
        json.dump(request.body(), f)


#endregion


#region 客户端信息管理相关 API
@command.get("/command/clients/list")
async def list_client(request: Request):
    log.log("List clients from {client}.".format(
        client="{host}:{port}".format(host=request.client.host, port=request.client.port)), QuickValues.Log.info)
    return Datas.Clients.refresh()


@command.get("/command/clients/status")
async def status(request: Request):
    log.log("List clients status from {client}.".format(
        client="{host}:{port}".format(host=request.client.host, port=request.client.port)), QuickValues.Log.info)
    return Datas.ClientStatus.refresh()


@command.post("/command/clients/pro_register")
@command.put("/command/clients/pre_register")
@command.get("/command/clients/pre_register")
async def pre_register(id: str, request: Request):
    Datas.Clients.pre_register(id=id, conf=request)


#endregion


#region 指令下发 API
@command.get("/command/client/{client_uid}/restart")
async def restart(client_uid: str):
    await gRPC.command(client_uid, CommandTypes_pb2.RestartApp)


@command.get("/command/client/{client_uid}/send_notification")
async def send_notification(client_uid: str,
                            message_mask: str,
                            message_content: str,
                            overlay_icon_left: int = 0,
                            overlay_icon_right: int = 0,
                            is_emergency: bool = False,
                            is_speech_enabled: bool = True,
                            is_effect_enabled: bool = True,
                            is_sound_enabled: bool = True,
                            is_topmost: bool = True,
                            duration_seconds: float = 5.0,
                            repeat_counts: int = 1):
    await gRPC.command(client_uid, CommandTypes_pb2.SendNotification,
                       SendNotification_pb2.SendNotification(
                           MessageMask=message_mask,
                           MessageContent=message_content,
                           OverlayIconLeft=overlay_icon_left,
                           OverlayIconRight=overlay_icon_right,
                           IsEmergency=is_emergency,
                           IsSpeechEnabled=is_speech_enabled,
                           IsEffectEnabled=is_effect_enabled,
                           IsSoundEnabled=is_sound_enabled,
                           IsTopmost=is_topmost,
                           DurationSeconds=duration_seconds,
                           RepeatCounts=repeat_counts
                       ).SerializeToString())


@command.get("/command/client/{client_uid}/update_data")
async def update_data(client_uid: str):
    await gRPC.command(client_uid, CommandTypes_pb2.DataUpdated)


#endregion


#region 外部操作方法
@command.get("/api/refresh")
async def refresh() -> None:
    log.log("Settings refreshed.", QuickValues.Log.info)
    _ = Settings.refresh
    return None


#endregion


#region 启动函数
async def start(port: int = 50052):
    config = uvicorn.Config(app=command, port=port, host="0.0.0.0", log_level="error", access_log=False)
    server = uvicorn.Server(config)
    await server.serve()
    log.log("Command backend successfully start on {port}".format(port=port), QuickValues.Log.info)


#endregion
#endregion


#region Running directly processor
if __name__ == "__main__":
    log.log(message="Directly started, refused.", status=QuickValues.Log.error)
#endregion
