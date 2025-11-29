#! -*- coding:utf-8 -*-
import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config
from .ManagementServer.api import api as fastapi_app
from .ManagementServer.gRPC import grpc_app
from .database.connection import init_db


async def main_async():
    # Combine FastAPI and gRPC applications
    async def app(scope, receive, send):
        if scope["type"] == "http":
            await fastapi_app(scope, receive, send)
        elif scope["type"] == "grpc":
            await grpc_app(scope, receive, send)
        else:
            raise Exception("Unknown scope type")

    config = Config()
    config.bind = ["0.0.0.0:50050"]  # Set your desired host and port

    await serve(app, config)


def main():
    # region Presets
    # region 首次运行判定
    try:
        open(".installed").close()
        installed = True
    except FileNotFoundError:
        installed = False
    # endregiono

    # region 导入辅助库
    import argparse
    import json
    from json import JSONDecodeError
    import os

    # endregion

    # region 初始化数据目录
    for _folder in [
        "./logs",
    ]:
        try:
            os.mkdir(_folder)
        except FileExistsError:
            pass
    # endregion

    # region 检查项目信息配置
    try:
        with open("project_info.json") as f:
            json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        with open("project_info.json", "w") as f:
            json.dump(
                {
                    "name": "CIMS-backend",
                    "description": "ClassIsland Management Server on Python",
                    "author": "git@miniopensource.com",
                    "version": "1.2.0",
                    "url": "https://github.com/MINIOpenSource/CIMS-backend",
                },
                f,
            )
    # endregion

    # region 首次运行
    if not installed:
        _set = {
            "server": {
                "prefix": "http",
                "host": "localhost",
                "port": 50050,
            },
            "organization_name": "CIMS Default Organization",
        }

        with open("settings.json", "w") as s:
            json.dump(_set, s)

        open(".installed", "w").close()
    # endregion

    # region 传参初始化
    parser = argparse.ArgumentParser(
        description="ClassIsland Management Server Backend"
    )

    parser.add_argument(
        "-r",
        "--restore",
        action="store_true",
        help="Restore, and delete all existed data",
    )

    args = parser.parse_args()

    # endregion
    # endregion

    # region 操作函数
    if args.restore:
        if input("Continue?(y/n with default n)") in ("y", "Y"):
            import os

            os.remove(".installed")
            os.remove("settings.json")
    else:
        print("\033[2JWelcome to use CIMS.")
        init_db()  # Initialize the database
        asyncio.run(main_async())
    # endregion
