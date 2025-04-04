#! -*- coding:utf-8 -*-

#region Presets
import Datas  # 使用真实 Datas
import logger
import BuildInClasses  # 保留
import QuickValues
import json
import os
import time
import zipfile  # 用于打包
import io  # 用于内存流
from ManagementServer import gRPC  # 保留
# 导入 Protobuf (保留)
# ... (Protobuf imports) ...
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query, Body, Request, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse


# 导入 Settings 类 (假设在同级目录或 utils.py)
# from utils import _Settings
# 或者直接在这里定义 _Settings 类
# ... (在此处复制 _Settings 类的定义) ...
class _Settings:  # 临时定义，建议放共享文件
    """服务器设置管理类"""

    def __init__(self, config_path="settings.json"):
        self.conf_name: str = config_path
        self.conf_dict: dict = {}
        self._load_config()

    def _load_config(self):
        try:
            with open(self.conf_name, 'r', encoding='utf-8') as f:
                self.conf_dict = json.load(f)
            log.log(f"配置文件 {self.conf_name} 已加载/刷新。", QuickValues.Log.info)
        except FileNotFoundError:
            log.log(f"配置文件 {self.conf_name} 未找到。", QuickValues.Log.warning)
            self.conf_dict = {"gRPC": {}, "api": {}, "command": {}, "organization_name": "Default"}
        except json.JSONDecodeError:
            log.log(f"配置文件 {self.conf_name} 格式错误。", QuickValues.Log.error)
            self.conf_dict = {}

    async def refresh(self) -> dict:
        self._load_config(); return self.conf_dict

    @property
    def grpc_config(self) -> dict:
        return self.conf_dict.get("gRPC", {})

    @property
    def api_config(self) -> dict:
        return self.conf_dict.get("api", {})

    @property
    def command_config(self) -> dict:
        return self.conf_dict.get("command", {})

    @property
    def organization_name(self) -> str:
        return self.conf_dict.get("organization_name", "Default")

    @property
    def command_port(self) -> int:
        return self.command_config.get("port", 50052)

    @property
    def command_host(self) -> str:
        return self.command_config.get("host", "0.0.0.0")


Settings = _Settings()
log = logger.Logger()
RESOURCE_TYPES = ["ClassPlan", "DefaultSettings", "Policy", "Subjects", "TimeLayout"]
#endregion

command = FastAPI(title="CIMS Command API", description="用于管理服务器和下发指令的内部 API")
command.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


#region 配置文件管理 API (使用真实 Datas)

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


@command.delete("/command/datas/{resource_type}/delete", summary="删除配置文件", tags=["配置文件管理"])
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


@command.get("/command/datas/{resource_type}/list", summary="列出配置文件", tags=["配置文件管理"])
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


@command.put("/command/datas/{resource_type}/write", summary="写入配置文件", tags=["配置文件管理"])
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


#region 服务器配置和信息 API (从 api.py 移入)

@command.get("/command/server/settings", summary="获取服务器配置", tags=["服务器管理"])
async def get_settings() -> dict:
    """获取当前服务器的配置信息。"""
    log.log("请求获取服务器配置。", QuickValues.Log.info)
    await Settings.refresh()
    return Settings.conf_dict


@command.put("/command/server/settings", summary="更新服务器配置", tags=["服务器管理"])
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


@command.get("/command/server/info", summary="获取服务器信息", tags=["服务器管理"])
async def get_server_info() -> dict:
    """获取服务器的版本和组织名称等信息。"""
    log.log("请求服务器信息。", QuickValues.Log.info)
    await Settings.refresh()  # 确保组织名称最新
    # 版本号可以硬编码或从其他地方读取
    backend_version = "0.0.29 build 4 (Simulated)"  # 更新模拟版本
    return {
        "backend_version": backend_version,
        "organization_name": Settings.organization_name
    }


@command.get("/command/download/preset", summary="下载集控预设配置", tags=["数据操作"])
async def download_preset_config():
    """提供用于下载集控预设配置文件的接口。"""
    log.log("请求下载集控预设配置。", QuickValues.Log.info)
    preset_file_path = "cims_preset_config.zip"
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 添加默认配置文件（如果存在）或示例
            for res_type in RESOURCE_TYPES:
                try:
                    default_content = getattr(Datas, res_type).read("default")
                    zip_file.writestr(f"{res_type}/default.json",
                                      json.dumps(default_content, indent=4, ensure_ascii=False))
                except FileNotFoundError:
                    log.log(f"未找到默认 {res_type} 配置，跳过打包。", QuickValues.Log.debug)
                    # 可以选择添加一个空的或示例文件
                    # zip_file.writestr(f"{res_type}/default.json", json.dumps({"info": f"Default {res_type} placeholder"}, indent=4))
            try:
                with open("settings.json.example", "r", encoding="utf-8") as f_example:  # 假设有一个示例设置文件
                    zip_file.writestr("settings.json", f_example.read())
            except FileNotFoundError:
                zip_file.writestr("settings.json",
                                  json.dumps(Settings.conf_dict, indent=4, ensure_ascii=False))  # 或打包当前设置

        zip_buffer.seek(0)
        return StreamingResponse(zip_buffer, media_type="application/zip",
                                 headers={'Content-Disposition': f'attachment; filename="{preset_file_path}"'})
    except Exception as e:
        log.log(f"创建预设配置包时出错: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="服务器无法生成预设配置包。")


@command.get("/command/export/data", summary="导出服务器数据", tags=["数据操作"])
async def export_server_data():
    """提供用于导出服务器所有配置数据的接口。"""
    log.log("请求导出服务器数据。", QuickValues.Log.info)
    export_file_path = f"cims_export_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 打包所有配置文件
            data_dir = "Datas"
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith(".json"):  # 只打包 json 文件
                        file_path = os.path.join(root, file)
                        archive_path = os.path.relpath(file_path, data_dir)  # 在压缩包内的相对路径
                        log.log(f"Adding to export: {archive_path}", QuickValues.Log.debug)
                        zip_file.write(file_path, arcname=archive_path)
            # 打包服务器设置文件
            if os.path.exists(Settings.conf_name):
                log.log(f"Adding to export: {Settings.conf_name}", QuickValues.Log.debug)
                zip_file.write(Settings.conf_name, arcname=os.path.basename(Settings.conf_name))

        zip_buffer.seek(0)
        return StreamingResponse(zip_buffer, media_type="application/zip",
                                 headers={'Content-Disposition': f'attachment; filename="{export_file_path}"'})
    except Exception as e:
        log.log(f"导出服务器数据时发生错误: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="导出数据时发生内部错误。")


#endregion


#region 客户端信息管理 API (使用真实 Datas)

@command.get("/command/clients/list", summary="列出已注册客户端（UID）", tags=["客户端管理"])
async def list_clients(request: Request) -> list[str]:
    """获取所有已注册客户端的 UID 列表。"""
    log.log(f"来自 {request.client.host}:{request.client.port} 的请求，列出已注册客户端 UID。", QuickValues.Log.info)
    try:
        return list(Datas.Clients.refresh().keys())  # Clients.clients 是 dict
    except Exception as e:
        log.log(f"获取客户端列表时出错: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="获取客户端列表失败。")


@command.get("/command/clients/status", summary="获取客户端状态", tags=["客户端管理"])
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


@command.post("/command/clients/pre_register", summary="预注册客户端", tags=["客户端管理"])
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

#region 指令下发 API (保持不变或微调)
# ... (batch_client_action, restart, send_notification, update_data 基本不变, 确保它们调用的是模拟 gRPC 或真实 gRPC) ...
# 例如 send_notification 的 GET 版本移除，强制使用 POST/PUT
@command.post("/command/client/{client_uid}/send_notification", summary="发送通知", tags=["指令下发"])
async def send_notification_post(client_uid: str, notification_params: dict = Body(...)):
    """向指定客户端发送通知 (使用 POST Body 传递参数)。"""
    log.log(f"尝试向客户端 {client_uid} 发送通知 (POST): {notification_params}", QuickValues.Log.info)
    # 从 Body 中提取参数
    message_mask = notification_params.get('message_mask')
    message_content = notification_params.get('message_content')
    # ... 其他参数 ...
    if not message_mask or not message_content:
        raise HTTPException(status_code=400, detail="缺少 message_mask 或 message_content 参数。")

    try:
        # 构建 Protobuf (如果使用)
        # notification_data = SendNotification_pb2.SendNotification(...)
        # await gRPC.command(client_uid, CommandTypes_pb2.SendNotification, notification_data.SerializeToString())
        log.log(f"通知已发送至客户端 {client_uid} (模拟)。", QuickValues.Log.info)
        return {"message": f"通知已发送至客户端 {client_uid}。"}
    except Exception as e:
        log.log(f"发送通知至客户端 {client_uid} 失败: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail=f"发送指令失败: {e}")


#endregion

# 移除 /api/refresh 接口

#region 启动函数 (保持不变)
async def start(port: int = 50052, host: str = "0.0.0.0"):
    # ... (代码同前) ...
    cmd_port = Settings.command_port
    cmd_host = Settings.command_host
    config = uvicorn.Config(app=command, host=cmd_host, port=cmd_port, log_level="info", access_log=True)
    server = uvicorn.Server(config)
    log.log(f"Command API 服务器准备在 http://{cmd_host}:{cmd_port} 启动...", QuickValues.Log.info)
    await server.serve()
    log.log("Command API 服务器已停止。", QuickValues.Log.info)


if __name__ == "__main__":
    log.log("Command API 作为主脚本启动。", QuickValues.Log.info)
    cmd_port = Settings.command_port
    cmd_host = Settings.command_host
    uvicorn.run(command, host=cmd_host, port=cmd_port, log_level="info")
#endregion
