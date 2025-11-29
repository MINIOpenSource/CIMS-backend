#! -*- coding:utf-8 -*-

# region Presets
# region 导入项目内建库
from .. import logger
from .. import QuickValues
from ..database.connection import SessionLocal
from ..database.models import (
    Tenant,
    Resource,
    ProfileConfig,
    PreRegister,
    Client,
    ClientStatus,
)

# endregion


# region 导入辅助库
import json
import time
import asyncio

# endregion


# region 导入 gRPC 库
from ..ManagementServer import gRPC

# endregion


# region 导入 Protobuf 构建文件
from ..Protobuf.Command import (
    SendNotification_pb2,
)
from ..Protobuf.Enum import (
    CommandTypes_pb2,
)

# endregion


# region 导入 FastAPI 相关库
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query, Body, Request, HTTPException, Depends
from fastapi.responses import (
    FileResponse,
)


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
        try:
            self.conf_dict = json.load(open(self.conf_name))
        except FileNotFoundError:
            self.conf_dict = {}
        return self.conf_dict


Settings = _Settings()
# endregion


# region 定义 API 并声明 CORS
command = FastAPI()
command.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# endregion


# region 内建辅助函数和辅助参量
log = logger.Logger()
RESOURCE_TYPES = ["ClassPlan", "DefaultSettings", "Policy", "Subjects", "TimeLayout"]


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
            raise HTTPException(
                status_code=404, detail=f"Tenant '{tenant_name}' not found"
            )
        return tenant.id
    finally:
        session.close()


# endregion
# endregion


# region Main
# region 客户端配置文件管理相关 API (/command/datas/)
@command.get(
    "/command/datas/{resource_type}/create",
    summary="Create Configuration File",
    tags=["Configuration Management"],
)
async def create(
    resource_type: str, name: str, tenant_id: int = Depends(get_tenant_id)
):
    """Create a new configuration file."""
    if resource_type in RESOURCE_TYPES:
        log.log(
            f"Attempting to create config: type={resource_type}, name={name}",
            QuickValues.Log.info,
        )
        session = SessionLocal()
        try:
            existing = (
                session.query(Resource)
                .filter_by(tenant_id=tenant_id, resource_type=resource_type, name=name)
                .first()
            )
            if existing:
                log.log("Creation failed: Resource exists", QuickValues.Log.warning)
                raise HTTPException(status_code=409, detail="Resource already exists")

            new_resource = Resource(
                tenant_id=tenant_id, resource_type=resource_type, name=name, data={}
            )
            session.add(new_resource)
            session.commit()

            log.log(f"Config {resource_type}[{name}] created.", QuickValues.Log.info)
            return {"message": f"Config {resource_type}[{name}] created."}
        except Exception as e:
            session.rollback()
            log.log(
                f"Error creating config {resource_type}[{name}]: {e}",
                QuickValues.Log.error,
            )
            raise HTTPException(status_code=500, detail=f"Error creating file: {e}")
        finally:
            session.close()
    else:
        raise HTTPException(
            status_code=404, detail=f"Invalid resource type: {resource_type}"
        )


@command.delete("/command/datas/{resource_type}")
@command.delete("/command/datas/{resource_type}/")
@command.delete("/command/datas/{resource_type}/delete")
@command.get("/command/datas/{resource_type}/delete")
async def delete(
    resource_type: str, name: str, tenant_id: int = Depends(get_tenant_id)
):
    """Delete a specified configuration file."""
    if resource_type in RESOURCE_TYPES:
        log.log(
            f"Attempting to delete config: type={resource_type}, name={name}",
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
                log.log("Delete failed: Resource not found", QuickValues.Log.warning)
                raise HTTPException(status_code=404, detail="Resource not found")

            session.delete(resource)
            session.commit()

            log.log(f"Config {resource_type}[{name}] deleted.", QuickValues.Log.info)
            return {"message": f"Config {resource_type}[{name}] deleted."}
        except Exception as e:
            session.rollback()
            log.log(
                f"Error deleting config {resource_type}[{name}]: {e}",
                QuickValues.Log.error,
            )
            raise HTTPException(status_code=500, detail=f"Error deleting file: {e}")
        finally:
            session.close()
    else:
        raise HTTPException(
            status_code=404, detail=f"Invalid resource type: {resource_type}"
        )


@command.get("/command/datas/{resource_type}/list")
async def list_config_files(
    resource_type: str, tenant_id: int = Depends(get_tenant_id)
) -> list[str]:
    """List configuration files of a specific type."""
    if resource_type in RESOURCE_TYPES:
        log.log(
            f"Attempting to list configs: type={resource_type}", QuickValues.Log.info
        )
        session = SessionLocal()
        try:
            resources = (
                session.query(Resource)
                .filter_by(tenant_id=tenant_id, resource_type=resource_type)
                .all()
            )
            return [r.name for r in resources]
        except Exception as e:
            log.log(
                f"Error listing configs {resource_type}: {e}", QuickValues.Log.error
            )
            raise HTTPException(status_code=500, detail=f"Error listing files: {e}")
        finally:
            session.close()
    else:
        raise HTTPException(
            status_code=404, detail=f"Invalid resource type: {resource_type}"
        )


@command.put(
    "/command/datas/{resource_type}/rename",
    summary="Rename Configuration File",
    tags=["Configuration Management"],
)
async def rename(
    resource_type: str, name: str, target: str, tenant_id: int = Depends(get_tenant_id)
):
    """Rename a configuration file."""
    if resource_type in RESOURCE_TYPES:
        log.log(
            f"Attempting to rename config: type={resource_type}, old={name}, new={target}",
            QuickValues.Log.info,
        )
        if not target:
            raise HTTPException(status_code=400, detail="Target name cannot be empty.")

        session = SessionLocal()
        try:
            resource = (
                session.query(Resource)
                .filter_by(tenant_id=tenant_id, resource_type=resource_type, name=name)
                .first()
            )
            if not resource:
                raise HTTPException(status_code=404, detail="Source resource not found")

            existing = (
                session.query(Resource)
                .filter_by(
                    tenant_id=tenant_id, resource_type=resource_type, name=target
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=409, detail="Target resource already exists"
                )

            resource.name = target
            session.commit()

            log.log(
                f"Config {resource_type}[{name}] renamed to {target}.",
                QuickValues.Log.info,
            )
            return {"message": f"Config {resource_type}[{name}] renamed to {target}."}
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            log.log(
                f"Error renaming config {resource_type}[{name}]: {e}",
                QuickValues.Log.error,
            )
            raise HTTPException(status_code=500, detail=f"Error renaming file: {e}")
        finally:
            session.close()
    else:
        raise HTTPException(
            status_code=404, detail=f"Invalid resource type: {resource_type}"
        )


@command.put("/command/datas/{resource_type}")
@command.put("/command/datas/{resource_type}/")
@command.put("/command/datas/{resource_type}/write")
@command.post("/command/datas/{resource_type}")
@command.post("/command/datas/{resource_type}/")
@command.post("/command/datas/{resource_type}/write")
@command.get("/command/datas/{resource_type}/write")
async def write(
    resource_type: str,
    name: str,
    request: Request,
    tenant_id: int = Depends(get_tenant_id),
):
    """Write content to configuration file (Expects JSON Body)."""
    if resource_type in RESOURCE_TYPES:
        body = await request.body()
        content_length = len(body)
        log.log(
            f"Attempting to write config: type={resource_type}, name={name}, size={content_length} bytes",
            QuickValues.Log.info,
        )
        try:
            data_dict = json.loads(body.decode("utf-8"))

            session = SessionLocal()
            try:
                resource = (
                    session.query(Resource)
                    .filter_by(
                        tenant_id=tenant_id, resource_type=resource_type, name=name
                    )
                    .first()
                )
                if not resource:
                    # Auto-create if not exists? Or strict 404?
                    # Original logic implied existing files usually. Let's auto-create for robustness.
                    resource = Resource(
                        tenant_id=tenant_id,
                        resource_type=resource_type,
                        name=name,
                        data=data_dict,
                    )
                    session.add(resource)
                else:
                    resource.data = data_dict

                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

            log.log(
                f"Config {resource_type}[{name}] written {content_length} bytes.",
                QuickValues.Log.info,
            )
            return {
                "message": f"Config {resource_type}[{name}] written {content_length} bytes."
            }
        except json.JSONDecodeError:
            log.log(
                f"Write config {resource_type}[{name}] failed: Invalid JSON.",
                QuickValues.Log.error,
            )
            raise HTTPException(status_code=400, detail="Invalid JSON body.")
        except Exception as e:
            log.log(
                f"Write config {resource_type}[{name}] failed: {e}",
                QuickValues.Log.error,
            )
            raise HTTPException(status_code=500, detail=f"Error writing file: {e}")
    else:
        raise HTTPException(
            status_code=404, detail=f"Invalid resource type: {resource_type}"
        )


# endregion


# region 服务器配置文件管理相关 API (/command/server/)
@command.get("/command/server/settings")
async def get_settings() -> dict:
    """Get current server settings."""
    log.log("Requesting server settings.", QuickValues.Log.info)
    await Settings.refresh()
    return Settings.conf_dict


@command.put("/command/server/settings")
@command.post("/command/server/settings")
async def update_settings(request: Request):
    """Update server settings with JSON body."""
    log.log("Attempting to update server settings.", QuickValues.Log.critical)
    try:
        new_settings = await request.json()
        with open(Settings.conf_name, "w", encoding="utf-8") as f:
            json.dump(new_settings, f)
        await Settings.refresh()
        log.log("Server settings updated.", QuickValues.Log.info)
        return {"message": "Server settings updated successfully."}
    except json.JSONDecodeError:
        log.log("Update settings failed: Invalid JSON.", QuickValues.Log.error)
        raise HTTPException(status_code=400, detail="Invalid JSON body.")
    except IOError as e:
        log.log(f"Update settings failed: IO Error: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail=f"IO Error: {e}")


@command.get("/command/server/version")
async def version() -> dict:
    """Get server version and organization info."""
    log.log("Server ver gotten.", QuickValues.Log.info)
    await Settings.refresh()
    try:
        with open("project_info.json") as pi:
            return {
                "backend_version": json.load(pi)["version"],
                "organization_name": Settings.conf_dict.get(
                    "organization_name", "Unknown"
                ),
            }
    except FileNotFoundError:
        return {"backend_version": "Unknown", "organization_name": "Unknown"}


@command.get("/command/server/ManagementPreset.json")
async def mp():
    """Download management preset configuration."""
    log.log("Requesting management preset.", QuickValues.Log.info)
    # Ensure keys exist or handle defaults
    api_conf = Settings.conf_dict.get("api", {})
    grpc_conf = Settings.conf_dict.get("gRPC", {})

    with open("ManagementPreset.json", "w") as mp:
        json.dump(
            {
                "ManagementServerKind": 1,
                "ManagementServer": "{prefix}://{host}:{port}".format(
                    prefix=api_conf.get("prefix", "http"),
                    host=api_conf.get("host", "localhost"),
                    port=api_conf.get("mp_port", 50050),
                ),
                "ManagementServerGrpc": "{prefix}://{host}:{port}".format(
                    prefix=grpc_conf.get("prefix", "http"),
                    host=grpc_conf.get("host", "localhost"),
                    port=grpc_conf.get("mp_port", 50051),
                ),
            },
            mp,
        )
    return FileResponse("ManagementPreset.json")


@command.get("/command/server/export")
def export_server_data():
    """Export all server configuration data."""
    raise NotImplementedError


# endregion


# region 客户端信息管理相关 API (/command/clients/)
@command.get("/command/clients/list")
async def list_clients(
    request: Request, tenant_id: int = Depends(get_tenant_id)
) -> list[str]:
    """Get list of registered client UIDs."""
    log.log(
        f"Request from {request.client.host}:{request.client.port} to list client UIDs.",
        QuickValues.Log.info,
    )
    session = SessionLocal()
    try:
        clients = session.query(Client).filter_by(tenant_id=tenant_id).all()
        return [c.uid for c in clients]
    except Exception as e:
        log.log(f"Error listing clients: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="Error listing clients.")
    finally:
        session.close()


@command.get("/command/clients/status")
async def list_client_status(
    request: Request, tenant_id: int = Depends(get_tenant_id)
) -> list[dict]:
    """Get comprehensive status of all clients."""
    log.log(
        f"Request from {request.client.host}:{request.client.port} to get client status.",
        QuickValues.Log.info,
    )
    session = SessionLocal()
    try:
        clients = session.query(Client).filter_by(tenant_id=tenant_id).all()
        statuses = session.query(ClientStatus).filter_by(tenant_id=tenant_id).all()
        status_map = {s.uid: s for s in statuses}

        result = []
        for client in clients:
            s = status_map.get(client.uid)
            status_str = "offline"
            last_seen = None

            if s and s.is_online:
                status_str = "online"

            if s and s.last_heartbeat:
                try:
                    last_seen = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(s.last_heartbeat)
                    )
                except ValueError:
                    last_seen = "Invalid Timestamp"

            result.append(
                {
                    "uid": client.uid,
                    "name": client.client_id,  # Assuming client_id maps to name or hardware ID
                    "status": status_str,
                    "last_seen": last_seen,
                }
            )

        return result
    except Exception as e:
        log.log(f"Error getting client status: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="Error getting client status.")
    finally:
        session.close()


@command.post("/command/clients/pre_register")
@command.put("/command/clients/pre_register")
@command.get("/command/clients/pre_register")
async def pre_register_client(
    data: dict = Body(...), tenant_id: int = Depends(get_tenant_id)
):
    """Pre-register a client with configuration."""
    client_id = data.get("id")
    config = data.get("config")
    if not client_id:
        raise HTTPException(status_code=400, detail="Missing client ID 'id'.")
    if config is not None and not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="'config' must be a dictionary.")

    log.log(f"Attempting to pre-register client: ID={client_id}", QuickValues.Log.info)

    session = SessionLocal()
    try:
        existing = (
            session.query(PreRegister)
            .filter_by(tenant_id=tenant_id, client_id=client_id)
            .first()
        )
        if existing:
            existing.config = config if config else {}
        else:
            new_prereg = PreRegister(
                tenant_id=tenant_id,
                client_id=client_id,
                config=config if config else {},
            )
            session.add(new_prereg)

        session.commit()
        log.log(f"Client {client_id} pre-registered.", QuickValues.Log.info)
        return {"message": f"Client {client_id} pre-registered successfully."}
    except Exception as e:
        session.rollback()
        log.log(f"Pre-register failed for {client_id}: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail=f"Pre-register failed: {e}")
    finally:
        session.close()


@command.get(
    "/command/clients/pre_registered/list",
    summary="List Pre-registered Clients",
    tags=["Client Management"],
)
async def list_pre_registered_clients(
    request: Request, tenant_id: int = Depends(get_tenant_id)
) -> list[dict]:
    """List all pre-registered clients."""
    log.log(
        f"Request from {request.client.host}:{request.client.port} to list pre-registered clients.",
        QuickValues.Log.info,
    )
    session = SessionLocal()
    try:
        preregs = session.query(PreRegister).filter_by(tenant_id=tenant_id).all()
        return [{"id": p.client_id, "config": p.config} for p in preregs]
    except Exception as e:
        log.log(f"Error listing pre-registered clients: {e}", QuickValues.Log.error)
        raise HTTPException(
            status_code=500, detail="Error listing pre-registered clients."
        )
    finally:
        session.close()


@command.delete(
    "/command/clients/pre_registered/delete",
    summary="Delete Pre-registered Client",
    tags=["Client Management"],
)
async def delete_pre_registered_client(
    client_id: str = Query(..., description="ID of client to delete"),
    tenant_id: int = Depends(get_tenant_id),
):
    """Delete a pre-registered client."""
    log.log(
        f"Attempting to delete pre-registered client: ID={client_id}",
        QuickValues.Log.info,
    )
    session = SessionLocal()
    try:
        prereg = (
            session.query(PreRegister)
            .filter_by(tenant_id=tenant_id, client_id=client_id)
            .first()
        )
        if prereg:
            session.delete(prereg)
            session.commit()
            log.log(f"Pre-registered client {client_id} deleted.", QuickValues.Log.info)
            return {"message": f"Pre-registered client {client_id} deleted."}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Pre-registered client '{client_id}' not found.",
            )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        log.log(
            f"Delete pre-registered client {client_id} failed: {e}",
            QuickValues.Log.error,
        )
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")
    finally:
        session.close()


@command.put(
    "/command/clients/pre_registered/update",
    summary="Update Pre-registered Client",
    tags=["Client Management"],
)
async def update_pre_registered_client(
    data: dict = Body(...), tenant_id: int = Depends(get_tenant_id)
):
    """Update configuration for a pre-registered client."""
    client_id = data.get("id")
    config = data.get("config")
    if not client_id:
        raise HTTPException(status_code=400, detail="Missing client ID 'id'.")
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="'config' must be a dictionary.")

    log.log(
        f"Attempting to update pre-registered client: ID={client_id}",
        QuickValues.Log.info,
    )
    session = SessionLocal()
    try:
        prereg = (
            session.query(PreRegister)
            .filter_by(tenant_id=tenant_id, client_id=client_id)
            .first()
        )
        if prereg:
            prereg.config = config
            session.commit()
            log.log(f"Pre-registered client {client_id} updated.", QuickValues.Log.info)
            return {"message": f"Pre-registered client {client_id} updated."}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Pre-registered client '{client_id}' not found.",
            )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        log.log(
            f"Update pre-registered client {client_id} failed: {e}",
            QuickValues.Log.error,
        )
        raise HTTPException(status_code=500, detail=f"Update failed: {e}")
    finally:
        session.close()


# endregion


# region 客户端管理 API (/command/client/)
# region 客户端信息管理 API
@command.get(
    "/command/client/{client_uid}/details",
    summary="Get Client Details",
    tags=["Client Management"],
)
async def get_client_details(
    client_uid: str, request: Request, tenant_id: int = Depends(get_tenant_id)
) -> dict:
    """Get detailed info of a client."""
    log.log(
        f"Request from {request.client.host}:{request.client.port} for details of {client_uid}.",
        QuickValues.Log.info,
    )
    session = SessionLocal()
    try:
        client = (
            session.query(Client).filter_by(tenant_id=tenant_id, uid=client_uid).first()
        )
        status = (
            session.query(ClientStatus)
            .filter_by(tenant_id=tenant_id, uid=client_uid)
            .first()
        )
        profile = (
            session.query(ProfileConfig)
            .filter_by(tenant_id=tenant_id, uid=client_uid)
            .first()
        )

        if not client:
            # Check pre-register
            prereg = (
                session.query(PreRegister)
                .filter_by(tenant_id=tenant_id, client_id=client_uid)
                .first()
            )  # Assuming uid might match client_id or similar logic
            if prereg:
                return {
                    "uid": client_uid,
                    "name": "Pre-registered Device",
                    "status": "pre-registered",
                    "config_profile": prereg.config,
                }
            else:
                raise HTTPException(
                    status_code=404, detail=f"Client {client_uid} not found."
                )

        status_str = "offline"
        last_seen = None
        if status:
            status_str = "online" if status.is_online else "offline"
            if status.last_heartbeat:
                try:
                    last_seen = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(status.last_heartbeat)
                    )
                except Exception:
                    pass

        return {
            "uid": client.uid,
            "name": client.client_id,
            "status": status_str,
            "last_seen": last_seen,
            "config_profile": profile.config if profile else {},
        }

    except HTTPException:
        raise
    except Exception as e:
        log.log(f"Error getting details for {client_uid}: {e}", QuickValues.Log.error)
        raise HTTPException(status_code=500, detail="Error getting client details.")
    finally:
        session.close()


# endregion


# region 客户端指令下发 API
@command.get("/command/client/{client_uid}/restart")
async def restart(client_uid: str, tenant_id: int = Depends(get_tenant_id)):
    # TODO: Verify tenant ownership of client_uid before sending
    await gRPC.command(client_uid, CommandTypes_pb2.RestartApp)


@command.get("/command/client/{client_uid}/send_notification")
async def send_notification(
    client_uid: str,
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
    repeat_counts: int = 1,
    tenant_id: int = Depends(get_tenant_id),
):
    # TODO: Verify tenant ownership
    await gRPC.command(
        client_uid,
        CommandTypes_pb2.SendNotification,
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
            RepeatCounts=repeat_counts,
        ).SerializeToString(),
    )


@command.get("/command/client/{client_uid}/update_data")
async def update_data(client_uid: str, tenant_id: int = Depends(get_tenant_id)):
    # TODO: Verify tenant ownership
    await gRPC.command(client_uid, CommandTypes_pb2.DataUpdated)


@command.post("/command/client/batch_action")
async def batch_action(data: dict = Body(...), tenant_id: int = Depends(get_tenant_id)):
    # TODO: Pass tenant_id to helper functions
    action = data.get("action")
    client_uids = data.get("client_uids", [])

    # Ideally verify all UIDs belong to tenant_id here

    if action == "send_notification":
        await asyncio.gather(
            *[
                send_notification(uid, tenant_id=tenant_id, **data.get("payload"))
                for uid in client_uids
            ]
        )
    elif action == "restart":
        await asyncio.gather(
            *[restart(uid, tenant_id=tenant_id) for uid in client_uids]
        )
    elif action == "update_data":
        await asyncio.gather(
            *[update_data(uid, tenant_id=tenant_id) for uid in client_uids]
        )


# endregion


# endregion


# region 外部操作方法
@command.get("/api/refresh")
async def refresh() -> None:
    log.log("Settings refreshed.", QuickValues.Log.info)
    _ = Settings.refresh
    return None


# endregion


# region 启动函数
async def start(port: int = 50052):
    config = uvicorn.Config(
        app=command, port=port, host="0.0.0.0", log_level="error", access_log=False
    )
    server = uvicorn.Server(config)
    await server.serve()
    log.log(
        "Command backend successfully start on {port}".format(port=port),
        QuickValues.Log.info,
    )


# endregion
# endregion


# region Running directly processor
if __name__ == "__main__":
    log.log(message="Directly started, refused.", status=QuickValues.Log.error)
# endregion
