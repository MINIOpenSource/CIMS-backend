#! -*- coding:utf-8 -*-

#region Presets
import Datas  # 使用真实的 Datas 模块
import logger
import BuildInClasses  # 保留，即使未使用
import QuickValues
import time
import json
import os
from typing import Optional, Dict, Any
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query, Request, HTTPException


# 导入 Settings 类 (假设在同级目录或 utils.py)
# from utils import _Settings
# 或者直接在这里定义 _Settings 类
# ... (在此处复制 _Settings 类的定义) ...
class _Settings:  # 临时定义，建议放共享文件
    """服务器设置管理类（API 端简化版，只关心 API 配置）"""

    def __init__(self, config_path="settings.json"):
        self.conf_name: str = config_path
        self.conf_dict: dict = {}
        self._load_config()

    def _load_config(self):
        try:
            with open(self.conf_name, 'r', encoding='utf-8') as f:
                self.conf_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # API 端即使加载失败，也应尽量提供默认值
            self.conf_dict = {"api": {"host": "localhost", "port": 50050, "prefix": "http"}}

    @property
    def api_config(self) -> dict:
        return self.conf_dict.get("api", {"host": "localhost", "port": 50050, "prefix": "http"})

    @property
    def api_host(self) -> str:
        return os.environ.get("CIMS_API_HOST", self.api_config.get("host", "localhost"))

    @property
    def api_port(self) -> int:
        return self.api_config.get("port", 50050)

    @property
    def api_prefix(self) -> str:
        return self.api_config.get("prefix", "http")

    async def refresh(self) -> dict:
        self._load_config()
        return self.conf_dict


Settings = _Settings()
log = logger.Logger()
RESOURCE_TYPES = ["ClassPlan", "DefaultSettings", "Policy", "Subjects", "TimeLayout"]
#endregion

api = FastAPI(title="CIMS Client API", description="供 ClassIsland 客户端使用的配置拉取 API")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"]
)


async def _get_manifest_entry(base_url_path: str, name: str, version: int, host: str, port: int, prefix: str) -> dict:
    """生成 Manifest 中的单个资源条目，包含协议前缀。"""
    host_prefix = prefix + "://" if prefix else "http://"  # 默认 http

    port_str = f":{port}"
    if (host_prefix == "http://" and port == 80) or \
            (host_prefix == "https://" and port == 443):
        port_str = ""

    return {
        "Value": f"{host_prefix}{host}{port_str}{base_url_path}?name={name}",
        "Version": version,
    }


@api.get("/api/v1/client/{client_uid}/manifest", summary="获取客户端配置清单", tags=["客户端配置"])
async def manifest(client_uid: str, version: Optional[int] = None) -> dict:
    """为指定的客户端提供配置清单 (Manifest)。"""
    log.log(f"客户端 {client_uid} 请求配置清单。", QuickValues.Log.info)
    await Settings.refresh()  # 确保 API 配置是最新的

    if version is None:
        version = int(time.time())

    host = Settings.api_host
    port = Settings.api_port
    prefix = Settings.api_prefix

    # 从真实的 Datas 获取配置策略
    profile_config = Datas.ProfileConfig.profile_config.get(client_uid)
    if not profile_config:
        # 如果客户端没有特定配置，尝试获取预注册信息（如果客户端是首次连接）
        # 注意：api.py 通常不知道客户端是否是首次连接，这个逻辑可能需要在注册时处理
        # 这里简化为：如果没有特定配置，则使用默认值
        log.log(f"客户端 {client_uid} 未找到特定配置，使用默认配置。", QuickValues.Log.debug)
        profile_config = {
            "ClassPlan": "default", "TimeLayout": "default", "Subjects": "default",
            "Settings": "default", "Policy": "default"
        }

    config_map = {
        "ClassPlanSource": ("/api/v1/client/ClassPlan", profile_config.get("ClassPlan", "default")),
        "TimeLayoutSource": ("/api/v1/client/TimeLayout", profile_config.get("TimeLayout", "default")),
        "SubjectsSource": ("/api/v1/client/Subjects", profile_config.get("Subjects", "default")),
        "DefaultSettingsSource": ("/api/v1/client/DefaultSettings", profile_config.get("Settings", "default")),
        "PolicySource": ("/api/v1/client/Policy", profile_config.get("Policy", "default")),
    }

    manifest_dict = {}
    for key, (path, name) in config_map.items():
        manifest_dict[key] = await _get_manifest_entry(path, name, version, host, port, prefix)

    manifest_dict["ServerKind"] = 1  # 服务器类型保持不变
    # manifest_dict["OrganizationName"] = "从 Command API 获取" # 组织名称由客户端另外获取或硬编码在客户端

    log.log(f"为客户端 {client_uid} 生成的 Manifest: {manifest_dict}", QuickValues.Log.debug)
    return manifest_dict


@api.get("/api/v1/client/{resource_type}", summary="获取具体配置文件", tags=["客户端配置"])
async def get_resource(resource_type: str, name: str) -> dict:
    """获取具体的配置文件内容。"""
    if resource_type in RESOURCE_TYPES:
        log.log(f"请求配置文件：类型={resource_type}, 名称={name}", QuickValues.Log.info)
        try:
            # 使用真实的 Datas 模块读取
            config_data = getattr(Datas, resource_type).read(name)
            return config_data
        except FileNotFoundError as e:
            log.log(f"配置文件未找到：类型={resource_type}, 名称={name}. Error: {e}", QuickValues.Log.error)
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            log.log(f"读取配置文件时发生错误：类型={resource_type}, 名称={name}, 错误={e}", QuickValues.Log.error)
            raise HTTPException(status_code=500, detail=f"读取资源时发生内部错误。")
    else:
        log.log(f"请求失败：无效的资源类型 {resource_type}", QuickValues.Log.error)
        raise HTTPException(status_code=404, detail=f"无效的资源类型: {resource_type}")


# 移除 /api/refresh, /api/v1/server/* 等接口

# --- 启动函数 (保持不变) ---
async def start(port: int = 50050, host: str = "0.0.0.0"):
    # ... (代码同前) ...
    # 使用 Settings 获取端口和主机
    api_port = Settings.api_port
    api_host = Settings.api_host
    config = uvicorn.Config(app=api, host=api_host, port=api_port, log_level="info", access_log=True)
    server = uvicorn.Server(config)
    log.log(f"Client API 服务器准备在 {Settings.api_prefix}://{api_host}:{api_port} 启动...", QuickValues.Log.info)
    await server.serve()
    log.log("Client API 服务器已停止。", QuickValues.Log.info)


if __name__ == "__main__":
    log.log("Client API 作为主脚本启动。", QuickValues.Log.info)
    api_port = Settings.api_port
    api_host = Settings.api_host
    uvicorn.run(api, host=api_host, port=api_port, log_level="info")
