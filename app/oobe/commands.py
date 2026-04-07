"""CLI 子命令分发器。

将 argparse 解析结果路由到对应的命令处理函数。
包括 daemon 生命周期管理（daemon / start / stop / startup / monit）
和数据管理类命令（user / account / role / quota / config / reserved-name）。
"""

import sys


def dispatch(args) -> None:
    """根据子命令分发到对应处理器。"""
    cmd = args.command
    handlers = {
        "init": _h_init,
        "daemon": _h_daemon,
        "start": _h_start,
        "stop": _h_stop,
        "restart": _h_restart,
        "startup": _h_startup,
        "monit": _h_monit,
        "status": _h_status,
        "version": _h_version,
        "user": _h_user,
        "account": _h_account,
        "role": _h_role,
        "quota": _h_quota,
        "config": _h_config,
        "reserved-name": _h_reserved,
        "db-migrate": _h_migrate,
    }
    h = handlers.get(cmd)
    if h:
        h(args)
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


def _h_init(_a):
    """处理 init 子命令。"""
    from app.oobe.cmd_init import handle_init

    handle_init()


def _h_daemon(_a):
    """处理 daemon 子命令（前台运行服务）。"""
    from app.oobe.cmd_daemon import handle_daemon

    handle_daemon()


def _h_start(_a):
    """处理 start 子命令（启动服务）。"""
    from app.oobe.cmd_start import handle_start

    handle_start()


def _h_stop(_a):
    """处理 stop 子命令（停止服务）。"""
    from app.oobe.cmd_stop import handle_stop

    handle_stop()


def _h_restart(_a):
    """处理 restart 子命令（重启服务）。"""
    from app.oobe.cmd_restart import handle_restart

    handle_restart()


def _h_startup(_a):
    """处理 startup 子命令（开关开机自启）。"""
    from app.oobe.cmd_startup import handle_startup

    handle_startup()


def _h_monit(_a):
    """处理 monit 子命令（监控日志）。"""
    from app.oobe.cmd_monit import handle_monit

    handle_monit()


def _h_status(_a):
    """检查系统状态。"""
    from app.oobe.detector import is_initialized

    s = "✅ 已初始化" if is_initialized() else "❌ 未初始化"
    print(s)


def _h_version(_a):
    """显示版本号。"""
    print("CIMS Backend v0.1.0")


def _h_user(a):
    """用户管理子命令。"""
    from app.oobe.cmd_user import handle_user

    handle_user(a)


def _h_account(a):
    """账户管理子命令。"""
    from app.oobe.cmd_account import handle_account

    handle_account(a)


def _h_role(a):
    """角色管理子命令。"""
    from app.oobe.cmd_role import handle_role

    handle_role(a)


def _h_quota(a):
    """限额管理子命令。"""
    from app.oobe.cmd_quota import handle_quota

    handle_quota(a)


def _h_config(a):
    """配置管理子命令。"""
    from app.oobe.cmd_config import handle_config

    handle_config(a)


def _h_reserved(a):
    """保留名管理子命令。"""
    from app.oobe.cmd_reserved import handle_reserved

    handle_reserved(a)


def _h_migrate(_a):
    """执行数据库迁移。"""
    import subprocess

    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        check=True,
    )
