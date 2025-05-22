#! -*- coding:utf-8 -*-
"""
CIMS (ClassIsland 管理服务器) API 的 FastAPI 应用程序。

本模块定义了用于客户端配置分发、设置刷新等外部操作的 API 端点,
并管理服务器的启动。它使用 FastAPI 创建 Web API,并使用 uvicorn 为应用程序提供服务。
"""

#region Presets
#region 导入项目内建库
import Datas
import logger
import BuildInClasses
import QuickValues
#endregion


#region 导入辅助库
import time
import json
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
    """
    管理从 JSON 配置文件加载的 API 服务器设置。
    """
    def __init__(self):
        """
        通过从 "settings.json" 加载来初始化设置。
        """
        self.conf_name: str = "settings.json"
        self.conf_dict: dict = json.load(open(self.conf_name))

    async def refresh(self) -> dict:
        """
        从配置文件重新加载设置。

        返回:
            dict: 重新加载后的设置字典。
        """
        self.conf_dict = json.load(open(self.conf_name))
        return self.conf_dict


Settings = _Settings()
#endregion


#region 定义 API
# 初始化 FastAPI 应用程序并添加 CORS 中间件。
api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


#endregion


#region 内建辅助函数和辅助参量
async def _get_manifest_entry(base_url: str, name: str, version: int, host: str, port: int) -> dict:
    """
    生成清单条目字典。

    参数:
        base_url (str): 资源的基础 URL。
        name (str): 资源的名称。
        version (int): 资源的版本。
        host (str): 服务器的主机名。
        port (int): 服务器的端口号。

    返回:
        dict: 表示清单条目的字典。
    """
    return {
        "Value": "{host}:{port}{base_url}?name={name}".format(
            base_url=base_url, name=name, host=host, port=port),
        "Version": version, }


log = logger.Logger()


#endregion
#endregion


#region 主程序
#region 配置文件分发 APIs
@api.get("/api/v1/client/{client_uid}/manifest")
async def manifest(client_uid: str | None = None, version: int = int(time.time())) -> dict:
    """
    提供客户端清单,其中包含指向各种配置文件的 URL。

    参数:
        client_uid (str | None, optional): 客户端的唯一标识符。默认为 None。
        version (int, optional): 清单条目的版本时间戳。默认为当前时间。

    返回:
        dict: 包含不同配置资源清单条目的字典。
    """
    log.log("客户端 {client_uid} 获取清单。".format(client_uid=client_uid), QuickValues.Log.info)
    host = (Settings.conf_dict.get("api", {}).get("prefix", "http") + "://" +
            Settings.conf_dict.get("api", {}).get("host", "127.0.0.1"))
    port = Settings.conf_dict.get("api", {}).get("mp_port", 50050)

    profile_config = Datas.ProfileConfig.refresh()
    base_url = "/api/v1/client/"
    config = profile_config.get(client_uid, {"ClassPlan": "default", "TimeLayout": "default", "Subjects": "default",
                                             "Settings": "default", "Policy": "default"})
    return {
        "ClassPlanSource": await _get_manifest_entry(f"{base_url}ClassPlan", config["ClassPlan"], version, host, port),
        "TimeLayoutSource": await _get_manifest_entry(f"{base_url}TimeLayout", config["TimeLayout"], version, host,
                                                      port),
        "SubjectsSource": await _get_manifest_entry(f"{base_url}Subjects", config["Subjects"], version, host, port),
        "DefaultSettingsSource": await _get_manifest_entry(f"{base_url}DefaultSettings", config["Settings"], version,
                                                           host, port),
        "PolicySource": await _get_manifest_entry(f"{base_url}Policy", config["Policy"], version, host, port),
        "ServerKind": 1,
        "OrganizationName": Settings.conf_dict.get("api", {}).get("OrganizationName", "CIMS 默认组织"),
    }


@api.get("/api/v1/client/{resource_type}")
async def policy(resource_type: str, name: str) -> dict:
    """
    根据资源类型和名称提供特定的配置文件。

    参数:
        resource_type (str): 请求的资源类型 (例如 "ClassPlan", "Policy")。
        name (str): 特定配置文件的名称。

    引发:
        HTTPException: 如果 resource_type 无效。

    返回:
        dict: 请求的配置文件的内容。
    """
    match resource_type:
        case "ClassPlan" | "DefaultSettings" | "Policy" | "Subjects" | "TimeLayout":
            log.log("获取 {resource_type}[{name}]。".format(resource_type=resource_type, name=name),
                    QuickValues.Log.info)
            return getattr(Datas, resource_type).read(name)
        case _:
            log.log("获取意外的 {resource_type}[{name}]。".format(resource_type=resource_type, name=name),
                    QuickValues.Log.error)
            raise HTTPException(status_code=404)


#endregion


#region 外部操作方法
@api.get("/api/refresh")
async def refresh() -> None:
    """
    通过重新加载配置文件来刷新服务器设置。
    """
    log.log("设置已刷新。", QuickValues.Log.info)
    _ = await Settings.refresh() # 确保对异步函数使用 await
    return None


#endregion


#region 启动函数
async def start(port: int = 50050):
    """
    使用 uvicorn 启动 FastAPI 应用程序服务器。

    参数:
        port (int, optional): 服务器运行的端口号。默认为 50050。
    """
    config = uvicorn.Config(app=api, port=port, host="0.0.0.0", log_level="debug")
    server = uvicorn.Server(config)
    await server.serve()
    log.log("API 服务器成功启动于端口 {port}".format(port=port), QuickValues.Log.info)


#endregion
#endregion


#region 直接执行处理
# 处理脚本被直接运行时的情况 (不允许)。
if __name__ == "__main__":
    log.log(message="脚本被直接启动,已拒绝。", status=QuickValues.Log.error)
#endregion
