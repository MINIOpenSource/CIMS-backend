#! -*- coding:utf-8 -*-
"""
FastAPI application for CIMS (ClassIsland Management Server) API.

This module defines the API endpoints for client configuration distribution,
external operations like settings refresh, and manages server startup.
It uses FastAPI for creating web APIs and uvicorn for serving the application.
"""

#region Presets
#region Import project built-in libraries
import Datas
import logger
import BuildInClasses
import QuickValues
#endregion


#region Import auxiliary libraries
import time
import json
#endregion


#region Import FastAPI related libraries
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query
from fastapi.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, PlainTextResponse, RedirectResponse, \
    StreamingResponse
from fastapi.exceptions import HTTPException


#endregion


#region Import configuration file
class _Settings:
    """
    Manages API server settings loaded from a JSON configuration file.
    """
    def __init__(self):
        """
        Initializes settings by loading them from "settings.json".
        """
        self.conf_name: str = "settings.json"
        self.conf_dict: dict = json.load(open(self.conf_name))

    async def refresh(self) -> dict:
        """
        Reloads the settings from the configuration file.

        Returns:
            dict: The reloaded settings dictionary.
        """
        self.conf_dict = json.load(open(self.conf_name))
        return self.conf_dict


Settings = _Settings()
#endregion


#region Define API
# Initializes the FastAPI application and adds CORS middleware.
api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


#endregion


#region Built-in helper functions and parameters
async def _get_manifest_entry(base_url: str, name: str, version: int, host: str, port: int) -> dict:
    """
    Generates a manifest entry dictionary.

    Args:
        base_url (str): The base URL for the resource.
        name (str): The name of the resource.
        version (int): The version of the resource.
        host (str): The host of the server.
        port (int): The port of the server.

    Returns:
        dict: A dictionary representing the manifest entry.
    """
    return {
        "Value": "{host}:{port}{base_url}?name={name}".format(
            base_url=base_url, name=name, host=host, port=port),
        "Version": version, }


log = logger.Logger()


#endregion
#endregion


#region Main
#region Configuration file distribution APIs
@api.get("/api/v1/client/{client_uid}/manifest")
async def manifest(client_uid: str | None = None, version: int = int(time.time())) -> dict:
    """
    Provides the client manifest with URLs to various configuration files.

    Args:
        client_uid (str | None, optional): The unique identifier of the client. Defaults to None.
        version (int, optional): The version timestamp for the manifest entries. Defaults to current time.

    Returns:
        dict: A dictionary containing manifest entries for different configuration resources.
    """
    log.log("Client {client_uid} get manifest.".format(client_uid=client_uid), QuickValues.Log.info)
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
        "OrganizationName": Settings.conf_dict.get("api", {}).get("OrganizationName", "CIMS default organization"),
    }


@api.get("/api/v1/client/{resource_type}")
async def policy(resource_type: str, name: str) -> dict:
    """
    Serves specific configuration files based on resource type and name.

    Args:
        resource_type (str): The type of the resource requested (e.g., "ClassPlan", "Policy").
        name (str): The name of the specific configuration file.

    Raises:
        HTTPException: If the resource_type is invalid.

    Returns:
        dict: The content of the requested configuration file.
    """
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


#region External operation methods
@api.get("/api/refresh")
async def refresh() -> None:
    """
    Refreshes the server settings by reloading the configuration file.
    """
    log.log("Settings refreshed.", QuickValues.Log.info)
    _ = await Settings.refresh() # Ensure await is used for async function
    return None


#endregion


#region Start function
async def start(port: int = 50050):
    """
    Starts the FastAPI application server using uvicorn.

    Args:
        port (int, optional): The port number to run the server on. Defaults to 50050.
    """
    config = uvicorn.Config(app=api, port=port, host="0.0.0.0", log_level="debug")
    server = uvicorn.Server(config)
    await server.serve()
    log.log("API server successfully start on {port}".format(port=port), QuickValues.Log.info)


#endregion
#endregion


#region Direct execution handler
# Handles the case where the script is run directly, which is not allowed.
if __name__ == "__main__":
    log.log(message="Directly started, refused.", status=QuickValues.Log.error)
#endregion
