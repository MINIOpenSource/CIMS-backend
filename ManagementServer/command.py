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
import time
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
from fastapi import FastAPI, Query, Body, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, PlainTextResponse, RedirectResponse, \
    StreamingResponse


#endregion


#region 导入配置文件
class _Settings:
    def __init__(self):
        self.conf_name: str = "settings.json"
        self.conf_dict: dict = json.load(open(self.conf_name))

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
    allow_credentials=True,
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
#region 客户端配置文件管理相关 API (/command/datas/)
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
async def delete(resource_type: str, name: str):
    """删除指定的配置文件。"""
    if resource_type in RESOURCE_TYPES:
        log.log(f"尝试删除配置文件：类型={resource_type}, 名称={name}", QuickValues.Log.info)
        try:
            getattr(Datas, resource_type).delete(name)
            log.log(f"配置文件 {resource_type}[{name}] 已删除。", QuickValues.Log.info)
            return {"message": f"配置文件 {resource_type}[{name}] 已删除。"}
        except FileNotFoundError as e:
            log.log(f"删除失败：{e}", QuickValues.Log.warning)
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            log.log(f"删除配置文件 {resource_type}[{name}] 时发生错误: {e}", QuickValues.Log.error)
            raise HTTPException(status_code=500, detail=f"删除文件时出错: {e}")
    else:
        raise HTTPException(status_code=404, detail=f"无效的资源类型: {resource_type}")


@command.get("/command/datas/{resource_type}/list")
async def list_config_files(resource_type: str) -> list[str]:
    """列出指定类型的配置文件。"""
    if resource_type in RESOURCE_TYPES:
        log.log(f"尝试列出配置文件：类型={resource_type}", QuickValues.Log.info)
        try:
            # Datas.Resource.refresh() 返回列表
            return getattr(Datas, resource_type).refresh()
        except Exception as e:
            log.log(f"列出配置文件 {resource_type} 时发生错误: {e}", QuickValues.Log.error)
            raise HTTPException(status_code=500, detail=f"列出文件时出错: {e}")
    else:
        raise HTTPException(status_code=404, detail=f"无效的资源类型: {resource_type}")


@command.put("/command/datas/{resource_type}/rename", summary="重命名配置文件", tags=["配置文件管理"])
async def rename(resource_type: str, name: str, target: str):
    """重命名配置文件。"""
    if resource_type in RESOURCE_TYPES:
        log.log(f"尝试重命名配置文件：类型={resource_type}, 原名称={name}, 新名称={target}", QuickValues.Log.info)
        if not target:  # 目标名称不能为空
            raise HTTPException(status_code=400, detail="目标名称不能为空。")
        try:
            getattr(Datas, resource_type).rename(name, target)
            log.log(f"配置文件 {resource_type}[{name}] 已重命名为 {target}。", QuickValues.Log.info)
            return {"message": f"配置文件 {resource_type}[{name}] 已重命名为 {target}。"}
        except FileNotFoundError as e:
            log.log(f"重命名失败：{e}", QuickValues.Log.warning)
            raise HTTPException(status_code=404, detail=str(e))
        except FileExistsError as e:
            log.log(f"重命名失败：{e}", QuickValues.Log.warning)
            raise HTTPException(status_code=409, detail=str(e))  # 409 Conflict
        except Exception as e:
            log.log(f"重命名配置文件 {resource_type}[{name}] 时发生错误: {e}", QuickValues.Log.error)
            raise HTTPException(status_code=500, detail=f"重命名文件时出错: {e}")
    else:
        raise HTTPException(status_code=404, detail=f"无效的资源类型: {resource_type}")


@command.put("/command/datas/{resource_type}")
@command.put("/command/datas/{resource_type}/")
@command.put("/command/datas/{resource_type}/write")
@command.post("/command/datas/{resource_type}")
@command.post("/command/datas/{resource_type}/")
@command.post("/command/datas/{resource_type}/write")
@command.get("/command/datas/{resource_type}/write")
async def write(resource_type: str, name: str, request: Request):
    """写入配置文件内容 (期望 Body 为 JSON)。"""
    if resource_type in RESOURCE_TYPES:
        body = await request.body()
        content_length = len(body)
        log.log(f"尝试写入配置文件：类型={resource_type}, 名称={name}, 大小={content_length}字节", QuickValues.Log.info)
        try:
            # 将 body 解码并解析为 dict
            data_dict = json.loads(body.decode('utf-8'))
            getattr(Datas, resource_type).write(name, data_dict)  # Datas.Resource.write 需要 dict
            log.log(f"配置文件 {resource_type}[{name}] 已写入 {content_length} 字节。", QuickValues.Log.info)
            return {"message": f"配置文件 {resource_type}[{name}] 已写入 {content_length} 字节。"}
        except FileNotFoundError as e:
            log.log(f"写入失败：{e}", QuickValues.Log.warning)
            raise HTTPException(status_code=404, detail=str(e))
        except json.JSONDecodeError:
            log.log(f"写入配置文件 {resource_type}[{name}] 失败: 请求体不是有效的 JSON。", QuickValues.Log.error)
            raise HTTPException(status_code=400, detail="请求体不是有效的 JSON 数据。")
        except Exception as e:
            log.log(f"写入配置文件 {resource_type}[{name}] 失败: {e}", QuickValues.Log.error)
            raise HTTPException(status_code=500, detail=f"写入文件时出错: {e}")
    else:
        raise HTTPException(status_code=404, detail=f"无效的资源类型: {resource_type}")


#endregion


#region 服务器配置文件管理相关 API (/command/server/)
@command.get("/command/server/settings")
async def get_settings() -> dict:
    """获取当前服务器的配置信息。"""
    log.log("请求获取服务器配置。", QuickValues.Log.info)
    await Settings.refresh()
    return Settings.conf_dict


@command.put("/command/server/settings")
@command.post("/command/server/settings")
async def update_settings(request: Request):
    """使用请求体中的 JSON 数据更新服务器配置文件。"""
    log.log("尝试更新服务器配置。", QuickValues.Log.critical)
    try:
        new_settings = await request.json()
        # 可以在这里添加验证逻辑，确保新设置包含必要字段
        with open(Settings.conf_name, "w", encoding='utf-8') as f:
            json.dump(new_settings, f, indent=4, ensure_ascii=False)
        await Settings.refresh()
        log.log("服务器配置已更新。", QuickValues.Log.info)
        # 可能需要通知其他模块配置已更改
        return {"message": "服务器配置已成功更新。"}
    except json.JSONDecodeError:
        log.log("更新服务器配置失败：请求体不是有效的 JSON。", QuickValues.Log.error)
        raise HTTPException(status_code=400, detail="请求体不是有效的 JSON 数据。")
    except IOError as e:
        log.log(f"更新服务器配置失败：写入文件时发生错误: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail=f"写入配置文件时发生错误: {e}")


@command.get("/command/server/version")
async def version() -> dict:
    """获取服务器的版本和组织名称等信息。"""
    log.log("Server ver gotten.", QuickValues.Log.info)
    await Settings.refresh()
    with open("project_info.json") as pi:
        return {
            "backend_version": json.load(pi)["version"],
            "organization_name": Settings.conf_dict["organization_name"]
        }


@command.get("/command/server/ManagementPreset.json")
async def mp():
    """提供用于下载集控预设配置文件的接口。"""
    log.log("请求下载集控预设配置。", QuickValues.Log.info)
    with open("ManagementPreset.json", "w") as mp:
        json.dump({
            "ManagementServerKind": 1,
            "ManagementServer": "{prefix}://{host}:{port}".format(prefix=Settings.conf_dict["api"]["prefix"],
                                                                  host=Settings.conf_dict["api"]["host"],
                                                                  port=Settings.conf_dict["api"]["mp_port"]),
            "ManagementServerGrpc": "{prefix}://{host}:{port}".format(prefix=Settings.conf_dict["gRPC"]["prefix"],
                                                                      host=Settings.conf_dict["gRPC"]["host"],
                                                                      port=Settings.conf_dict["gRPC"]["mp_port"])
        }, mp)
    return FileResponse("ManagementPreset.json")


@command.get("/command/server/export")
def export_server_data():
    """提供用于导出服务器所有配置数据的接口。"""
    raise NotImplementedError


#endregion


#region 客户端信息管理相关 API (/command/clients/)
@command.get("/command/clients/list")
async def list_clients(request: Request) -> list[str]:
    """获取所有已注册客户端的 UID 列表。"""
    log.log(f"来自 {request.client.host}:{request.client.port} 的请求，列出已注册客户端 UID。", QuickValues.Log.info)
    try:
        return list(Datas.Clients.refresh().keys())  # Clients.clients 是 dict
    except Exception as e:
        log.log(f"获取客户端列表时出错: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="获取客户端列表失败。")

@command.get("/command/clients/status")
async def list_client_status(request: Request) -> list[dict]:
    """获取所有客户端的综合状态信息（包括名称、UID、在线状态等）。"""
    log.log(f"来自 {request.client.host}:{request.client.port} 的请求，获取客户端状态。", QuickValues.Log.info)
    try:
        clients_data = Datas.Clients.refresh()  # uid: id (name)
        status_data = Datas.ClientStatus.refresh()  # uid: {isOnline, lastHeartbeat}
        result = []
        known_uids = set(clients_data.keys()) | set(status_data.keys())

        for uid in known_uids:
            client_info = {
                "uid": uid,
                "name": clients_data.get(uid, "未知名称"),  # 从 clients.json 获取名称
                "status": "unknown",
                "last_seen": None
            }
            if uid in status_data:
                client_info["status"] = "online" if status_data[uid].get("isOnline", False) else "offline"
                last_hb = status_data[uid].get("lastHeartbeat")
                if last_hb:
                    # 转换为易读的时间格式
                    try:
                        client_info["last_seen"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_hb))
                    except ValueError:  # 时间戳可能无效
                        client_info["last_seen"] = "无效时间戳"
            else:
                # 在 clients.json 中但不在 status.json 中的，视为从未连接或状态未知
                client_info["status"] = "unknown"

            result.append(client_info)

        return result
    except Exception as e:
        log.log(f"获取客户端状态时出错: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="获取客户端状态失败。")


@command.post("/command/clients/pro_register")
@command.put("/command/clients/pre_register")
@command.get("/command/clients/pre_register")
async def pre_register_client(data: dict = Body(...)):
    """预先注册一个客户端，并指定其配置。 Body: {"id": "client_id", "config": {"ClassPlan": ...}}"""
    client_id = data.get("id")
    config = data.get("config")
    if not client_id:
        raise HTTPException(status_code=400, detail="缺少客户端 ID 'id'。")
    if config is not None and not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="'config' 必须是一个字典。")

    log.log(f"尝试预注册客户端：ID={client_id}, 配置={config}", QuickValues.Log.info)
    try:
        # Datas.ProfileConfig.pre_register 会处理 None config
        Datas.ProfileConfig.pre_register(id=client_id, conf=config)
        log.log(f"客户端 {client_id} 已预注册。", QuickValues.Log.info)
        return {"message": f"客户端 {client_id} 已成功预注册。"}
    except Exception as e:
        log.log(f"预注册客户端 {client_id} 失败: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail=f"预注册失败: {e}")


@command.get("/command/clients/pre_registered/list", summary="列出预注册客户端", tags=["客户端管理"])
async def list_pre_registered_clients(request: Request) -> list[dict]:
    """获取所有已预注册但尚未连接的客户端及其配置。"""
    log.log(f"来自 {request.client.host}:{request.client.port} 的请求，列出预注册客户端。", QuickValues.Log.info)
    try:
        # 从 Datas.ProfileConfig 读取 pre_registers
        pre_reg_data = Datas.ProfileConfig.pre_registers
        # 转换为列表格式
        result = [{"id": id, "config": config} for id, config in pre_reg_data.items()]
        return result
    except Exception as e:
        log.log(f"获取预注册列表时出错: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="获取预注册列表失败。")


@command.delete("/command/clients/pre_registered/delete", summary="删除预注册客户端", tags=["客户端管理"])
async def delete_pre_registered_client(client_id: str = Query(..., description="要删除的预注册客户端 ID")):
    """删除一个预注册的客户端条目。"""
    log.log(f"尝试删除预注册客户端：ID={client_id}", QuickValues.Log.info)
    try:
        if client_id in Datas.ProfileConfig.pre_registers:
            del Datas.ProfileConfig.pre_registers[client_id]
            # 持久化更改
            with open("Datas/pre_register.json", "w", encoding="utf-8") as f:
                json.dump(Datas.ProfileConfig.pre_registers, f, indent=4, ensure_ascii=False)
            log.log(f"预注册客户端 {client_id} 已删除。", QuickValues.Log.info)
            return {"message": f"预注册客户端 {client_id} 已成功删除。"}
        else:
            raise HTTPException(status_code=404, detail=f"预注册客户端 ID '{client_id}' 未找到。")
    except Exception as e:
        log.log(f"删除预注册客户端 {client_id} 失败: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail=f"删除预注册条目失败: {e}")


@command.put("/command/clients/pre_registered/update", summary="更新预注册客户端配置", tags=["客户端管理"])
async def update_pre_registered_client(data: dict = Body(...)):
    """更新一个已预注册客户端的配置。 Body: {"id": "client_id", "config": {"ClassPlan": ...}}"""
    client_id = data.get("id")
    config = data.get("config")
    if not client_id:
        raise HTTPException(status_code=400, detail="缺少客户端 ID 'id'。")
    if not isinstance(config, dict):  # config 必须提供且为字典
        raise HTTPException(status_code=400, detail="'config' 必须提供且为一个字典。")

    log.log(f"尝试更新预注册客户端配置：ID={client_id}, 新配置={config}", QuickValues.Log.info)
    try:
        if client_id in Datas.ProfileConfig.pre_registers:
            Datas.ProfileConfig.pre_registers[client_id] = config
            # 持久化更改
            with open("Datas/pre_register.json", "w", encoding="utf-8") as f:
                json.dump(Datas.ProfileConfig.pre_registers, f, indent=4, ensure_ascii=False)
            log.log(f"预注册客户端 {client_id} 的配置已更新。", QuickValues.Log.info)
            return {"message": f"预注册客户端 {client_id} 的配置已成功更新。"}
        else:
            raise HTTPException(status_code=404, detail=f"预注册客户端 ID '{client_id}' 未找到。")
    except Exception as e:
        log.log(f"更新预注册客户端 {client_id} 失败: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail=f"更新预注册条目失败: {e}")


#endregion


#region 客户端管理 API (/command/client/)
#region 客户端信息管理 API
@command.get("/command/client/{client_uid}/details", summary="获取单个客户端详情", tags=["客户端管理"])
async def get_client_details(client_uid: str, request: Request) -> dict:
    """获取指定客户端的详细信息，包括配置。"""
    log.log(f"来自 {request.client.host}:{request.client.port} 的请求，获取客户端 {client_uid} 的详情。",
            QuickValues.Log.info)
    try:
        # 组合来自 status 和 profile_config 的信息
        all_statuses = await list_client_status(request)  # 复用上面的函数获取基本状态
        client_detail = next((client for client in all_statuses if client["uid"] == client_uid), None)

        if not client_detail:
            # 也许只在 pre_register 里？
            pre_reg_info = Datas.ProfileConfig.pre_registers.get(client_uid)
            if pre_reg_info:
                client_detail = {"uid": client_uid, "name": "预注册设备", "status": "pre-registered",
                                 "config_profile": pre_reg_info}
            else:
                raise HTTPException(status_code=404, detail=f"客户端 {client_uid} 未找到。")

        # 获取配置信息
        profile_config = Datas.ProfileConfig.profile_config.get(client_uid, {})
        client_detail["config_profile"] = profile_config

        # 可以补充其他信息，例如从 gRPC 连接状态获取 IP 等（如果 gRPC 层提供）
        # client_detail["ip_address"] = gRPC.get_client_ip(client_uid) # 假设有此方法

        return client_detail
    except HTTPException:
        raise  # 重新抛出 404
    except Exception as e:
        log.log(f"获取客户端 {client_uid} 详情时出错: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="获取客户端详情失败。")


#endregion


#region 客户端指令下发 API
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
