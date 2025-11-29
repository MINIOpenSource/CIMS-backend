#! -*- coding:utf-8 -*-


# region Presets
# region 导入项目内建库
from .. import logger
from .. import QuickValues
from ..database.connection import SessionLocal
from ..database.models import Tenant, ProfileConfig, Resource

# endregion


# region 导入辅助库
import time
import json

# endregion


# region 导入 FastAPI 相关库
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import HTTPException


# endregion


# region 导入配置文件
class _Settings:
    def __init__(self):
        self.conf_name: str = "settings.json"
        try:
            self.conf_dict: dict = json.load(open(self.conf_name))
        except FileNotFoundError:
            self.conf_dict = {}

    async def refresh(self) -> dict:
        self.conf_dict = json.load(open(self.conf_name))
        return self.conf_dict


Settings = _Settings()
# endregion


# region Dependency for multi-tenancy
def get_tenant_id(request: Request) -> int:
    """
    Extracts tenant ID from the request hostname.
    Assumes subdomain as tenant name.
    """
    hostname = request.headers.get("host", "").split(":")[0]
    # Default to 'default' if no subdomain or IP access, need better logic for prod
    parts = hostname.split(".")
    tenant_name = parts[0] if len(parts) > 1 else "default"

    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter_by(name=tenant_name).first()
        if not tenant:
            # Fallback or error
            # For now error
            raise HTTPException(
                status_code=404, detail=f"Tenant '{tenant_name}' not found"
            )
        return tenant.id
    finally:
        session.close()


# endregion

# region 定义 API
api = FastAPI()
api.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# endregion


# region 内建辅助函数和辅助参量
async def _get_manifest_entry(base_url, name, version, host, port):
    return {
        "Value": "{host}:{port}{base_url}?name={name}".format(
            base_url=base_url, name=name, host=host, port=port
        ),
        "Version": version,
    }


log = logger.Logger()


# endregion
# endregion


# region Main
# region 配置文件分发 APIs
@api.get("/api/v1/client/{client_uid}/manifest")
async def manifest(
    client_uid: str | None = None,
    version: int = int(time.time()),
    tenant_id: int = Depends(get_tenant_id),
) -> dict:
    log.log(
        "Client {client_uid} get manifest for tenant {tenant_id}.".format(
            client_uid=client_uid, tenant_id=tenant_id
        ),
        QuickValues.Log.info,
    )
    host = (
        Settings.conf_dict.get("api", {}).get("prefix", "http")
        + "://"
        + Settings.conf_dict.get("api", {}).get("host", "127.0.0.1")
    )
    port = Settings.conf_dict.get("api", {}).get("mp_port", 50050)

    # Fetch profile config from DB
    session = SessionLocal()
    try:
        profile = (
            session.query(ProfileConfig)
            .filter_by(tenant_id=tenant_id, uid=client_uid)
            .first()
        )
        if not profile:
            # Return default config or 404
            # For now returning empty/default structure
            config = {
                "ClassPlan": "default",
                "TimeLayout": "default",
                "Subjects": "default",
                "Settings": "default",
                "Policy": "default",
            }
        else:
            config = profile.config
    finally:
        session.close()

    base_url = "/api/v1/client/"

    return {
        "ClassPlanSource": await _get_manifest_entry(
            f"{base_url}ClassPlan",
            config.get("ClassPlan", "default"),
            version,
            host,
            port,
        ),
        "TimeLayoutSource": await _get_manifest_entry(
            f"{base_url}TimeLayout",
            config.get("TimeLayout", "default"),
            version,
            host,
            port,
        ),
        "SubjectsSource": await _get_manifest_entry(
            f"{base_url}Subjects",
            config.get("Subjects", "default"),
            version,
            host,
            port,
        ),
        "DefaultSettingsSource": await _get_manifest_entry(
            f"{base_url}DefaultSettings",
            config.get("Settings", "default"),
            version,
            host,
            port,
        ),
        "PolicySource": await _get_manifest_entry(
            f"{base_url}Policy", config.get("Policy", "default"), version, host, port
        ),
        "ServerKind": 1,
        "OrganizationName": Settings.conf_dict.get("api", {}).get(
            "OrganizationName", "CIMS default organization"
        ),
    }


@api.get("/api/v1/client/{resource_type}")
async def policy(
    resource_type, name: str, tenant_id: int = Depends(get_tenant_id)
) -> dict:
    if resource_type in (
        "ClassPlan",
        "DefaultSettings",
        "Policy",
        "Subjects",
        "TimeLayout",
    ):
        log.log(
            "{resource_type}[{name}] gotten for tenant {tenant_id}.".format(
                resource_type=resource_type, name=name, tenant_id=tenant_id
            ),
            QuickValues.Log.info,
        )

        session = SessionLocal()
        try:
            resource = (
                session.query(Resource)
                .filter_by(tenant_id=tenant_id, resource_type=resource_type, name=name)
                .first()
            )

            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")

            return resource.data
        finally:
            session.close()

    else:
        log.log(
            "Unexpected {resource_type}[{name}] gotten.".format(
                resource_type=resource_type, name=name
            ),
            QuickValues.Log.error,
        )
        raise HTTPException(status_code=404)


# endregion


# region 外部操作方法
@api.get("/api/refresh")
async def refresh() -> None:
    log.log("Settings refreshed.", QuickValues.Log.info)
    _ = Settings.refresh
    return None


# endregion


# region 启动函数
async def start(port: int = 50050):
    config = uvicorn.Config(app=api, port=port, host="0.0.0.0", log_level="debug")
    server = uvicorn.Server(config)
    await server.serve()
    log.log(
        "API server successfully start on {port}".format(port=port),
        QuickValues.Log.info,
    )


# endregion
# endregion


# region Running directly processor
if __name__ == "__main__":
    log.log(message="Directly started, refused.", status=QuickValues.Log.error)
# endregion
