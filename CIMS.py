#! -*- coding:utf-8 -*-

#region Only directly run allowed.
if __name__ != "__main__":
    import sys

    sys.exit(0)
#endregion


#region Presets
#region 首次运行判定
try:
    open(".installed").close()
    installed = True
except FileNotFoundError:
    installed = False
#endregiono


#region 导入辅助库
import argparse
import asyncio
import json
from json import JSONDecodeError
import os
import sys

#endregion


#region 初始化数据目录
for _folder in ["./logs", "./Datas", "./Datas/ClassPlan", "./Datas/DefaultSettings",
                "./Datas/Policy", "./Datas/Subjects", "./Datas/TimeLayout"]:
    try:
        os.mkdir(_folder)
    except FileExistsError:
        pass
#endregion


#region 检查数据文件
for _file in ["./settings.json"] + ["./Datas/{}.json".format(name) for
                                    name in ["client_status", "clients",
                                             "pre_register", "profile_config"]] + ["./Datas/{}/default.json".format(
    name) for name in ["ClassPlan", "DefaultSettings", "Policy", "Subjects", "TimeLayout"]]:
    try:
        with open(_file) as f:
            json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        with open(_file, "w") as f:
            f.write("{}")
#endregion


#region 检查项目信息配置
try:
    with open("project_info.json") as f:
        json.load(f)
except (FileNotFoundError, JSONDecodeError):
    with open("project_info.json", "w") as f:
        json.dump({
            "name": "CIMS-backend",
            "description": "ClassIsland Management Server on Python",
            "author": "kaokao221",
            "version": "1.1beta2",
            "url": "https://github.com/MINIOpenSource/CIMS-backend"
        }, f)
#endregion


#region 导入项目内建库
import Datas
import logger
import BuildInClasses
import QuickValues
import ManagementServer

#endregion


#region 首次运行
if installed:
    with open("settings.json") as s:
        _set = json.load(s)
else:
    _set = {
        "gRPC": {
            "prefix": "http",
            "host": "localhost",
            "mp_port": 50051,
            "port": 50051
        },
        "api": {
            "prefix": "http",
            "host": "localhost",
            "mp_port": 50050,
            "port": 50050
        },
        "command": {
            "prefix": "http",
            "host": "localhost",
            "mp_port": 50052,
            "port": 50052
        },
        "organization_name": "CIMS Default Organization",
    }

    for part in ["gRPC", "api", "command"]:
        _input = input(
            "{part} host and port used in ManagementPreset.json "
            "(formatted as {prefix}://{host}:{port} and port must be given)"
            "(Enter directly to use default settings):".format(part=part,
                                                               prefix=_set[part]["prefix"],
                                                               host=_set[part]["host"],
                                                               port=_set[part]["mp_port"]))
        _part_set = True
        while _part_set:
            try:
                if _input.startswith("http://"):
                    print("HTTP is not safe and HTTPS recommended.\n" if not _input.startswith(
                        "http://localhost") else "",
                          end="")
                if not _input.startswith(("https://", "http://")):
                    raise ValueError
                _set[part]["prefix"] = _input.split(":")[0] + "://"
                _set[part]["host"] = _input.split(":")[1][2:]
                _set[part]["mp_port"] = int(_input.split(":")[2])
                # if _set[part]["port"] not in list(range(-1, 65536)):
                #     raise KeyError
                _part_set = False
            except (IndexError, ValueError):
                if _input == "":
                    _part_set = False
                else:
                    _input = input("Invalid input, retry:")
            except KeyError:
                _input = input("Invalid input, retry:")
        if _input != "":
            _input = input("{part} listening port(Enter directly to use the same as above):".format(part=part))
            _part_set = True
            while _part_set:
                try:
                    _set[part]["port"] = int(_input)
                    _part_set = False
                except ValueError:
                    if _input == "":
                        _set[part]["port"] = _set[part]["mp_port"]
                        _part_set = False
                    else:
                        _input = input("Invalid port, retry:")
        else:
            _set[part]["port"] = _set[part]["mp_port"]
            pass

    _input = input("Organization name:")
    _set["organization_name"] = _input if _input != "" else "CIMS Default Organization"

    with open("settings.json", "w") as s:
        json.dump(_set, s)

    open(".installed", "w").close()


    async def refresh():
        await asyncio.gather(
            ManagementServer.command.Settings.refresh(),
            ManagementServer.api.Settings.refresh(),
            ManagementServer.gRPC.Settings.refresh()
        )


    asyncio.run(refresh())
#endregion


#region 传参初始化
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


#region 启动器
async def start():
    await asyncio.gather(
        ManagementServer.gRPC.start(_set["gRPC"]["port"]),
        ManagementServer.api.start(_set["api"]["port"]),
        ManagementServer.command.start(_set["command"]["port"]),
    )


#endregion


#region 操作函数
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
    print("\033[2JWelcome to use CIMS1.0v1sp0patch1")
    asyncio.run(start())
#endregion
