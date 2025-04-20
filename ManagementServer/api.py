#! -*- coding:utf-8 -*-


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
    def __init__(self):
        self.conf_name: str = "settings.json"
        self.conf_dict: dict = json.load(open(self.conf_name))

    async def refresh(self) -> dict:
        self.conf_dict = json.load(open(self.conf_name))
        return self.conf_dict


Settings = _Settings()
#endregion


#region 定义 API
api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


#endregion


#region 内建辅助函数和辅助参量
async def _get_manifest_entry(base_url, name, version, host, port):
    return {
        "Value": "{host}:{port}{base_url}?name={name}".format(
            base_url=base_url, name=name, host=host, port=port),
        "Version": version, }


log = logger.Logger()


#endregion
#endregion


#region Main
#region 配置文件分发 APIs
@api.get("/api/v1/client/{client_uid}/manifest")
async def manifest(client_uid: str | None = None, version: int = int(time.time())) -> dict:
    log.log("Client {client_uid} get manifest.".format(client_uid=client_uid), QuickValues.Log.info)
    host = (Settings.conf_dict.get("api", {}).get("prefix", "http") + "://" +
            Settings.conf_dict.get("api").get("host", "127.0.0.1"))
    port = Settings.conf_dict.get("api", {}).get("mp_port", 50050)

    """获取指定客户端的配置清单"""
    profile_config = Datas.ProfileConfig.profile_config
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
        "OrganizationName": Settings.conf_dict.get("api", {}).get("OrganizationName", "CIMS default organization"),
    }


@api.get("/api/v1/client/{resource_type}")
async def policy(resource_type, name: str) -> dict:
    match resource_type:
        case "ClassPlan" | "DefaultSettings" | "Policy" | "Subjects" | "TimeLayout":
            log.log("{resource_type}[{name}] gotten.".format(resource_type=resource_type, name=name),
                    QuickValues.Log.info)
            return getattr(Datas, resource_type).read(name)
        case _:
            log.log("Unexpected {resource_type}[{name}] gotten.".format(resource_type=resource_type, name=name),
                    QuickValues.Log.error)
            raise HTTPException(status_code=404)


#endregion


#region 外部操作方法
@api.get("/api/refresh")
async def refresh() -> None:
    log.log("Settings refreshed.", QuickValues.Log.info)
    _ = Settings.refresh
    return None


#endregion


#region 启动函数
async def start(port: int = 50050):
    config = uvicorn.Config(app=api, port=port, host="0.0.0.0", log_level="debug")
    server = uvicorn.Server(config)
    await server.serve()
    log.log("API server successfully start on {port}".format(port=port), QuickValues.Log.info)


#endregion
#endregion


#region Running directly processor
if __name__ == "__main__":
    log.log(message="Directly started, refused.", status=QuickValues.Log.error)
#endregion
