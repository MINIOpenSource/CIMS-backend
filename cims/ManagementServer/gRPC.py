#! -*- coding:utf-8 -*-

import grpc.aio
import time

from cims import logger
from cims import QuickValues
from cims.database.connection import SessionLocal
from cims.database.models import Tenant, Client, ClientStatus

# Import gRPC generated modules
from cims.Protobuf.Service import (
    ClientCommandDeliver_pb2_grpc,
    ClientRegister_pb2_grpc,
    Handshake_pb2_grpc,
    ConfigUpload_pb2_grpc,
    Audit_pb2_grpc,
)
from cims.Protobuf.Server import (
    ClientRegisterScRsp_pb2,
    HandshakeScRsp_pb2,
    ConfigUploadScRsp_pb2,
    AuditScRsp_pb2,
)
from cims.Protobuf.Client import (
    ClientRegisterCsReq_pb2,
    HandshakeScReq_pb2,
    ConfigUploadScReq_pb2,
    AuditScReq_pb2,
)
from cims.Protobuf.Enum import (
    Retcode_pb2,
    CommandTypes_pb2,
)

from cims.Protobuf.Server import (
    ClientCommandDeliverScRsp_pb2,
)
from fastapi import HTTPException

log = logger.Logger()


def _get_tenant_from_context(context: grpc.aio.ServicerContext):
    """
    Extracts tenant information from gRPC metadata.
    Expects 'host' metadata key, which usually contains the hostname.
    The tenant name is assumed to be the subdomain.
    """
    metadata = context.invocation_metadata()
    hostname = ""
    for m in metadata:
        if m.key == "host":
            hostname = m.value
            break

    # Extract subdomain as tenant name.
    # Example: tenant1.cims.com -> tenant1
    # Fallback to default if not present (logic can be adjusted)
    tenant_name = hostname.split(".")[0] if hostname else "default"

    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter_by(name=tenant_name).first()
        if not tenant:
            # Optionally create default tenant if it doesn't exist for initial setup
            # For strict multi-tenancy, this should abort.
            # Here we abort if not found.
            # Exception: 'localhost' or IP access might need handling.
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED, f"Tenant '{tenant_name}' not found."
            )
        return tenant
    finally:
        session.close()


class ClientCommandDeliverServicer(
    ClientCommandDeliver_pb2_grpc.ClientCommandDeliverServicer
):
    """
    Servicer for delivering commands to clients and handling long-lived connections.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ClientCommandDeliverServicer, cls).__new__(
                cls, *args, **kwargs
            )
            cls._instance.connected_clients = {}  # Map: client_uid -> grpc_context
        return cls._instance

    async def Deliver(self, request_iterator, context: grpc.aio.ServicerContext):
        """
        Bi-directional streaming RPC for command delivery.
        """
        # 1. Authenticate and identify tenant
        # Note: In an async generator, context.abort raises an exception that stops the generator.
        # We need to handle this carefully.
        try:
            tenant = _get_tenant_from_context(context)
        except Exception:
            # _get_tenant_from_context aborts, which raises an RpcError.
            # We assume it's handled by gRPC runtime.
            return

        # 2. Identify client from metadata
        metadata = context.invocation_metadata()
        client_uid = ""
        for m in metadata:
            if m.key == "cuid":
                client_uid = m.value
                break

        if not client_uid:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Client UID (cuid) missing in metadata.",
            )
            return

        log.log(
            f"Client {client_uid} connected to tenant {tenant.name}.",
            QuickValues.Log.info,
        )

        # Register connection
        self.connected_clients[client_uid] = context

        # Update status in DB
        session = SessionLocal()
        try:
            # Update or create client status
            status = (
                session.query(ClientStatus)
                .filter_by(tenant_id=tenant.id, uid=client_uid)
                .first()
            )
            if not status:
                status = ClientStatus(
                    tenant_id=tenant.id,
                    uid=client_uid,
                    is_online=True,
                    last_heartbeat=time.time(),
                )
                session.add(status)
            else:
                status.is_online = True
                status.last_heartbeat = time.time()
            session.commit()
        except Exception as e:
            log.log(
                f"Error updating status for {client_uid}: {e}", QuickValues.Log.error
            )
        finally:
            session.close()

        try:
            async for request in request_iterator:
                # Handle incoming messages from client (e.g. Heartbeat responses, command results)
                # Currently the proto definition for ClientCommandDeliverScReq might be minimal or generic.
                # Assuming basic structure based on previous logic.

                # Update heartbeat on any activity
                session = SessionLocal()
                try:
                    status = (
                        session.query(ClientStatus)
                        .filter_by(tenant_id=tenant.id, uid=client_uid)
                        .first()
                    )
                    if status:
                        status.last_heartbeat = time.time()
                        status.is_online = True
                        session.commit()
                finally:
                    session.close()

                # Echo logic (Placeholder)
                # If the client sends something, we might want to acknowledge it.
                # Currently just yielding nothing until we have commands to send.
                pass

        except Exception as e:
            log.log(f"Connection lost for {client_uid}: {e}", QuickValues.Log.warning)
        finally:
            # Cleanup
            self.connected_clients.pop(client_uid, None)
            session = SessionLocal()
            try:
                status = (
                    session.query(ClientStatus)
                    .filter_by(tenant_id=tenant.id, uid=client_uid)
                    .first()
                )
                if status:
                    status.is_online = False
                    session.commit()
            finally:
                session.close()


class ClientRegisterServicer(ClientRegister_pb2_grpc.ClientRegisterServicer):
    """
    Servicer for client registration.
    """

    async def Register(
        self,
        request: ClientRegisterCsReq_pb2.ClientRegisterCsReq,
        context: grpc.aio.ServicerContext,
    ):
        tenant = _get_tenant_from_context(context)

        # TODO: Add robust validation logic here (e.g., verify hardware ID signature)

        session = SessionLocal()
        try:
            client = (
                session.query(Client)
                .filter_by(tenant_id=tenant.id, uid=request.ClientUid)
                .first()
            )
            if client:
                log.log(
                    f"Client {request.ClientUid} re-registered.", QuickValues.Log.info
                )
                # Update info if needed
            else:
                new_client = Client(
                    tenant_id=tenant.id,
                    uid=request.ClientUid,
                    client_id=request.HardwareId,
                )
                session.add(new_client)
                session.commit()
                log.log(
                    f"New client registered: {request.ClientUid}", QuickValues.Log.info
                )

            return ClientRegisterScRsp_pb2.ClientRegisterScRsp(
                RetCode=Retcode_pb2.Success
            )
        except Exception as e:
            log.log(f"Registration failed: {e}", QuickValues.Log.error)
            return ClientRegisterScRsp_pb2.ClientRegisterScRsp(
                RetCode=Retcode_pb2.ServerInternalError
            )
        finally:
            session.close()


class HandshakeServicer(Handshake_pb2_grpc.HandshakeServicer):
    """
    Servicer for initial handshake.
    """

    async def Handshake(
        self,
        request: HandshakeScReq_pb2.HandshakeScReq,
        context: grpc.aio.ServicerContext,
    ):
        # tenant = _get_tenant_from_context(context) # Validate tenant
        # Logic for handshake (version check, etc.)
        return HandshakeScRsp_pb2.HandshakeScRsp(RetCode=Retcode_pb2.Success)


class ConfigUploadServicer(ConfigUpload_pb2_grpc.ConfigUploadServicer):
    """
    Servicer for uploading client configurations.
    """

    async def UploadConfig(
        self,
        request: ConfigUploadScReq_pb2.ConfigUploadScReq,
        context: grpc.aio.ServicerContext,
    ):
        # Logic to save config
        return ConfigUploadScRsp_pb2.ConfigUploadScRsp(RetCode=Retcode_pb2.Success)


class AuditServicer(Audit_pb2_grpc.AuditServicer):
    """
    Servicer for receiving audit events.
    """

    async def UploadAuditLog(
        self, request: AuditScReq_pb2.AuditScReq, context: grpc.aio.ServicerContext
    ):
        # Logic to save audit logs
        return AuditScRsp_pb2.AuditScRsp(RetCode=Retcode_pb2.Success)


# region 命令推送器
async def command(
    client_uid: str, command_type: CommandTypes_pb2.CommandTypes, payload: bytes = b""
):
    servicer = ClientCommandDeliverServicer()
    if client_uid not in servicer.connected_clients:
        log.log(
            "Send {command} to {client_uid}, failed.".format(
                command=command_type, client_uid=client_uid
            ),
            QuickValues.Log.error,
        )
        raise HTTPException(
            status_code=404, detail=f"Client not found or not connected: {client_uid}"
        )
    log.log(
        "Send {command} to {client_uid}".format(
            command=command_type, client_uid=client_uid
        ),
        QuickValues.Log.info,
    )

    try:
        # Construct the response object.
        # Note: We need to be careful about the exact field names of the new Proto.
        response = ClientCommandDeliverScRsp_pb2.ClientCommandDeliverScRsp(
            RetCode=Retcode_pb2.Success,
        )

        # Safe attribute setting
        if hasattr(response, "Type"):
            response.Type = command_type
        elif hasattr(response, "CommandType"):
            response.CommandType = command_type

        if hasattr(response, "Payload"):
            response.Payload = payload
        elif hasattr(response, "JsonPayload"):
            # If payload is bytes, maybe it goes elsewhere? Or ignoring if not supported
            pass

        await servicer.connected_clients[client_uid].write(response)

    except Exception as e:
        log.log(
            f"Failed to write to stream for {client_uid}: {e}", QuickValues.Log.error
        )
        servicer.connected_clients.pop(client_uid, None)
        raise HTTPException(status_code=500, detail=f"RPC Error: {e}")


# endregion

# Initialize gRPC App
grpc_app = grpc.aio.server()

ClientCommandDeliver_pb2_grpc.add_ClientCommandDeliverServicer_to_server(
    ClientCommandDeliverServicer(), grpc_app
)
ClientRegister_pb2_grpc.add_ClientRegisterServicer_to_server(
    ClientRegisterServicer(), grpc_app
)
Handshake_pb2_grpc.add_HandshakeServicer_to_server(HandshakeServicer(), grpc_app)
ConfigUpload_pb2_grpc.add_ConfigUploadServicer_to_server(
    ConfigUploadServicer(), grpc_app
)
Audit_pb2_grpc.add_AuditServicer_to_server(AuditServicer(), grpc_app)
