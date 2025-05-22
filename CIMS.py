#! -*- coding:utf-8 -*-
"""
CIMS (ClassIsland 管理服务器) 后端主脚本。

本脚本负责初始化并启动 CIMS 后端服务,包括 gRPC、API 和命令服务器。
它处理首次运行设置、数据目录初始化、配置加载以及命令行参数解析。
"""

#region Only directly run allowed.
if __name__ != "__main__":
    import sys

    sys.exit(0)
#endregion


#region Presets
#region 首次运行判定
# 通过检查 ".installed" 文件判断应用程序是否首次运行。
try:
    open(".installed").close()
    installed = True
except FileNotFoundError:
    installed = False
#endregion


#region 导入辅助库
import argparse
import asyncio
import json
from json import JSONDecodeError
import os
import sys
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from dotenv import load_dotenv

#endregion

#region Sentry 初始化
def initialize_sentry(dsn: str | None):
    """根据提供的 DSN 初始化 Sentry SDK。"""
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration()
            ],
            traces_sample_rate=1.0,  # 捕获所有事务以便进行性能监控
            profiles_sample_rate=1.0  # 捕获所有事务的性能分析数据
        )
        print("Sentry SDK 初始化成功。")
    else:
        print("未找到 SENTRY_DSN, Sentry SDK 未初始化。")

#endregion

#region 初始化辅助函数
def initialize_data_directories():
    """如果数据目录不存在,则创建它们。"""
    for _folder in ["./logs", "./Datas", "./Datas/ClassPlan", "./Datas/DefaultSettings",
                    "./Datas/Policy", "./Datas/Subjects", "./Datas/TimeLayout"]:
        try:
            os.mkdir(_folder)
        except FileExistsError:
            pass

def ensure_data_files_exist():
    """确保必要的 JSON 数据文件存在且为有效的 JSON 格式,如果不存在或格式无效则创建空文件。"""
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
    """确保 project_info.json 文件存在且为有效的 JSON 格式,如果不存在或格式无效则创建默认的项目信息文件。"""
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
    """刷新所有管理服务器的设置。"""
    await asyncio.gather(
        ManagementServer.command.Settings.refresh(),
        ManagementServer.api.Settings.refresh(),
        ManagementServer.gRPC.Settings.refresh()
    )

def perform_first_run_setup(settings_dict: dict) -> dict:
    """
    处理首次运行的设置过程,提示用户输入服务器配置和组织名称。
    修改并返回设置字典。

    参数:
        settings_dict (dict): 默认设置字典。

    返回:
        dict: 用户输入后的更新设置字典。
    """
    for part in ["gRPC", "api", "command"]:
        _input = input(
            "{part} 在 ManagementPreset.json 中使用的主机和端口 "
            "(格式为 {prefix}://{host}:{port} 且必须提供端口)"
            "(直接回车使用默认设置):".format(part=part,
                                                               prefix=settings_dict[part]["prefix"],
                                                               host=settings_dict[part]["host"],
                                                               port=settings_dict[part]["mp_port"]))
        _part_set = True
        while _part_set:
            try:
                if _input.startswith("http://"):
                    print("HTTP 不安全,推荐使用 HTTPS。\n" if not _input.startswith(
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
                    _input = input("输入无效,请重试:")
            except KeyError: # 理论上不应发生,但为稳健性保留
                _input = input("输入无效 (KeyError),请重试:")
        if _input != "":
            _input_port = input("{part} 监听端口(直接回车使用与上述相同的端口):".format(part=part))
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
                        _input_port = input("端口无效,请重试:")
        else:
            settings_dict[part]["port"] = settings_dict[part]["mp_port"]

    _org_name_input = input("组织名称:")
    settings_dict["organization_name"] = _org_name_input if _org_name_input != "" else "CIMS Default Organization"

    with open("settings.json", "w") as s:
        json.dump(settings_dict, s)

    open(".installed", "w").close()
    return settings_dict
#endregion


#region 导入项目内建库
import Datas
import logger
import BuildInClasses
import QuickValues
import ManagementServer

#endregion


#region 首次运行
#endregion


#region 初始化
load_dotenv()  # 从 .env 文件加载环境变量
SENTRY_DSN = os.getenv("SENTRY_DSN")
initialize_sentry(SENTRY_DSN)

initialize_data_directories()
ensure_data_files_exist()
load_or_create_project_info()

# 如果 ".installed" 文件未找到,则处理首次运行的设置过程。
# 提示用户输入服务器配置和组织名称。
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


#region 传参初始化
# 初始化命令行参数解析器。
parser = argparse.ArgumentParser(
    description="ClassIsland 管理服务器后端"
)

parser.add_argument(
    "-g",
    "--generate-management-preset",
    action="store_true",
    help="在程序根目录生成 ManagementPreset.json。"
)

parser.add_argument(
    "-r",
    "--restore",
    action="store_true",
    help="恢复并删除所有现有数据。"
)

args = parser.parse_args()


#endregion
#endregion


#region 启动器
async def start():
    """启动 gRPC、API 和命令服务器。"""
    await asyncio.gather(
        ManagementServer.gRPC.start(_set["gRPC"]["port"]),
        ManagementServer.api.start(_set["api"]["port"]),
        ManagementServer.command.start(_set["command"]["port"]),
    )


#endregion


#region 操作函数
# 处理命令行参数以执行恢复数据或生成预设等操作。
if args.restore:
    if input("是否继续?(y/n, 默认为 n)") in ("y", "Y"):
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
