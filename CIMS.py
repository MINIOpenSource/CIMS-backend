#! -*- coding:utf-8 -*-
"""
CIMS (ClassIsland Management Server) Backend Main Script.

This script initializes and starts the CIMS backend, including gRPC, API, and command servers.
It handles first-time setup, data directory initialization, configuration loading,
and command-line argument parsing.
"""

#region Only directly run allowed.
if __name__ != "__main__":
    import sys

    sys.exit(0)
#endregion


#region Presets
#region First run detection
# Checks if the application has been run before by looking for a ".installed" file.
try:
    open(".installed").close()
    installed = True
except FileNotFoundError:
    installed = False
#endregion


#region Import auxiliary libraries
import argparse
import asyncio
import json
from json import JSONDecodeError
import os
import sys

#endregion

#region Helper Functions for Initialization
def initialize_data_directories():
    """Creates necessary data directories if they don't exist."""
    for _folder in ["./logs", "./Datas", "./Datas/ClassPlan", "./Datas/DefaultSettings",
                    "./Datas/Policy", "./Datas/Subjects", "./Datas/TimeLayout"]:
        try:
            os.mkdir(_folder)
        except FileExistsError:
            pass

def ensure_data_files_exist():
    """Ensures essential JSON data files exist and are valid JSON, creating empty ones if not."""
    files_to_check = ["./settings.json"] + \
                     ["./Datas/{}.json".format(name) for name in ["client_status", "clients", "pre_register", "profile_config"]] + \
                     ["./Datas/{}/default.json".format(name) for name in ["ClassPlan", "DefaultSettings", "Policy", "Subjects", "TimeLayout"]]
    for _file in files_to_check:
        try:
            with open(_file) as f:
                json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            with open(_file, "w") as f:
                f.write("{}")

def load_or_create_project_info():
    """Ensures project_info.json exists and is valid JSON, creating a default one if not."""
    try:
        with open("project_info.json") as f:
            json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        with open("project_info.json", "w") as f:
            json.dump({
                "name": "CIMS-backend",
                "description": "ClassIsland Management Server on Python",
                "author": "git@miniopensource.com",
                "version": "1.1beta2sp3",
                "url": "https://github.com/MINIOpenSource/CIMS-backend"
            }, f)

async def refresh_management_server_settings():
    """Refreshes settings for all management servers."""
    await asyncio.gather(
        ManagementServer.command.Settings.refresh(),
        ManagementServer.api.Settings.refresh(),
        ManagementServer.gRPC.Settings.refresh()
    )

def perform_first_run_setup(settings_dict: dict) -> dict:
    """
    Handles the first-time setup process by prompting the user for server configurations
    and organization name. Modifies and returns the settings dictionary.

    Args:
        settings_dict (dict): The default settings dictionary.

    Returns:
        dict: The updated settings dictionary after user input.
    """
    for part in ["gRPC", "api", "command"]:
        _input = input(
            "{part} host and port used in ManagementPreset.json "
            "(formatted as {prefix}://{host}:{port} and port must be given)"
            "(Enter directly to use default settings):".format(part=part,
                                                               prefix=settings_dict[part]["prefix"],
                                                               host=settings_dict[part]["host"],
                                                               port=settings_dict[part]["mp_port"]))
        _part_set = True
        while _part_set:
            try:
                if _input.startswith("http://"):
                    print("HTTP is not safe and HTTPS recommended.\n" if not _input.startswith(
                        "http://localhost") else "",
                          end="")
                if not _input.startswith(("https://", "http://")):
                    raise ValueError
                settings_dict[part]["prefix"] = _input.split(":")[0]
                settings_dict[part]["host"] = _input.split(":")[1][2:]
                settings_dict[part]["mp_port"] = int(_input.split(":")[2])
                _part_set = False
            except (IndexError, ValueError):
                if _input == "":
                    _part_set = False
                else:
                    _input = input("Invalid input, retry:")
            except KeyError: # Should not happen with current logic, but good for robustness
                _input = input("Invalid input (KeyError), retry:")
        if _input != "":
            _input_port = input("{part} listening port(Enter directly to use the same as above):".format(part=part))
            _port_set_loop = True
            while _port_set_loop:
                try:
                    settings_dict[part]["port"] = int(_input_port)
                    _port_set_loop = False
                except ValueError:
                    if _input_port == "":
                        settings_dict[part]["port"] = settings_dict[part]["mp_port"]
                        _port_set_loop = False
                    else:
                        _input_port = input("Invalid port, retry:")
        else:
            settings_dict[part]["port"] = settings_dict[part]["mp_port"]

    _org_name_input = input("Organization name:")
    settings_dict["organization_name"] = _org_name_input if _org_name_input != "" else "CIMS Default Organization"

    with open("settings.json", "w") as s:
        json.dump(settings_dict, s)

    open(".installed", "w").close()
    return settings_dict
#endregion


#region Import built-in project libraries
import Datas
import logger
import BuildInClasses
import QuickValues
import ManagementServer

#endregion


#region First run
#endregion


#region Initialization
initialize_data_directories()
ensure_data_files_exist()
load_or_create_project_info()

# Handles the first-time setup process if ".installed" file is not found.
# Prompts user for server configurations and organization name.
if installed:
    with open("settings.json") as s:
        _set = json.load(s)
else:
    default_settings = {
        "gRPC": {"prefix": "http", "host": "localhost", "mp_port": 50051, "port": 50051},
        "api": {"prefix": "http", "host": "localhost", "mp_port": 50050, "port": 50050},
        "command": {"prefix": "http", "host": "localhost", "mp_port": 50052, "port": 50052},
        "organization_name": "CIMS Default Organization",
    }
    _set = perform_first_run_setup(default_settings)
    asyncio.run(refresh_management_server_settings())
#endregion


#region Argument parsing initialization
# Initializes command-line argument parser.
parser = argparse.ArgumentParser(
    description="ClassIsland Management Server Backend"
)

parser.add_argument(
    "-g",
    "--generate-management-preset",
    action="store_true",
    help="Generate ManagementPreset.json on the program root."
)

parser.add_argument(
    "-r",
    "--restore",
    action="store_true",
    help="Restore, and delete all existed data"
)

args = parser.parse_args()


#endregion
#endregion


#region Starter
async def start():
    """Starts the gRPC, API, and command servers."""
    await asyncio.gather(
        ManagementServer.gRPC.start(_set["gRPC"]["port"]),
        ManagementServer.api.start(_set["api"]["port"]),
        ManagementServer.command.start(_set["command"]["port"]),
    )


#endregion


#region Operation functions
# Handles command-line arguments to perform actions like restoring data or generating presets.
if args.restore:
    if input("Continue?(y/n with default n)") in ("y", "Y"):
        import os

        os.remove(".installed")
        os.remove("settings.json")
        os.remove("ManagementPreset.json")
        # if input("Remove datas?"):
        #     # for _json in ["./Datas/client_status.json", "./Datas/clients.json", "./"]
        #     pass
elif args.generate_management_preset:
    with open("ManagementPreset.json", "w") as mp:
        json.dump({
            "ManagementServerKind": 1,
            "ManagementServer": "{prefix}://{host}:{port}".format(prefix=_set["api"]["prefix"],
                                                                  host=_set["api"]["host"],
                                                                  port=_set["api"]["mp_port"]),
            "ManagementServerGrpc": "{prefix}://{host}:{port}".format(prefix=_set["gRPC"]["prefix"],
                                                                      host=_set["gRPC"]["host"],
                                                                      port=_set["gRPC"]["mp_port"])
        }, mp)
else:
    print("\033[2JWelcome to use CIMS.")
    asyncio.run(start())
#endregion
