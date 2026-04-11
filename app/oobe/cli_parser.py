"""CLI 参数解析器定义。

注册所有 20+ 子命令及其参数。
"""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """构建完整的 CLI 参数解析器。"""
    p = argparse.ArgumentParser(prog="cims", description="CIMS 后端管理工具")
    sub = p.add_subparsers(dest="command")
    # 基础命令
    sub.add_parser("daemon", help="前台运行服务（供 systemd 管理）")
    sub.add_parser("start", help="启动服务（systemctl start）")
    sub.add_parser("stop", help="停止服务（systemctl stop）")
    sub.add_parser("restart", help="重启服务（systemctl restart）")
    sub.add_parser("startup", help="开关开机自启动")
    sub.add_parser("monit", help="监控滚动日志")
    sub.add_parser("status", help="检查状态")
    sub.add_parser("version", help="显示版本")
    # 用户管理
    _add_user_commands(sub)
    # 账户管理
    _add_account_commands(sub)
    # 角色管理
    _add_role_commands(sub)
    # 限额管理
    _add_quota_commands(sub)
    # 配置管理
    _add_config_commands(sub)
    # 保留名管理
    _add_reserved_commands(sub)
    # 数据库管理
    sub.add_parser("db-migrate", help="执行数据库迁移")
    return p


def _add_user_commands(sub) -> None:
    """注册用户管理子命令组。"""
    up = sub.add_parser("user", help="用户管理")
    us = up.add_subparsers(dest="user_action")
    us.add_parser("list", help="列出所有用户")
    # create
    cp = us.add_parser("create", help="创建新用户")
    cp.add_argument("--username", required=True)
    cp.add_argument("--email", required=True)
    cp.add_argument("--password", required=True)
    cp.add_argument("--role", default="normal")
    # delete
    dp = us.add_parser("delete", help="删除用户")
    dp.add_argument("--username", required=True)
    # ban / activate
    bp = us.add_parser("ban", help="封禁用户")
    bp.add_argument("--username", required=True)
    ap = us.add_parser("activate", help="激活用户")
    ap.add_argument("--username", required=True)
    # reset-password
    rp = us.add_parser("reset-password", help="重置密码")
    rp.add_argument("--username", required=True)
    rp.add_argument("--password", required=True)
    # set-role
    sp = us.add_parser("set-role", help="设置角色")
    sp.add_argument("--username", required=True)
    sp.add_argument("--role", required=True)


def _add_account_commands(sub) -> None:
    """注册账户管理子命令组。"""
    ap = sub.add_parser("account", help="账户管理")
    a_sub = ap.add_subparsers(dest="account_action")
    a_sub.add_parser("list", help="列出所有账户")
    cp = a_sub.add_parser("create", help="创建账户")
    cp.add_argument("--name", required=True)
    cp.add_argument("--slug", required=True)
    dp = a_sub.add_parser("delete", help="删除账户")
    dp.add_argument("--slug", required=True)
    mp = a_sub.add_parser("add-member", help="添加成员")
    mp.add_argument("--slug", required=True)
    mp.add_argument("--username", required=True)
    mp.add_argument("--role", default="member")
    rp = a_sub.add_parser("remove-member", help="移除成员")
    rp.add_argument("--slug", required=True)
    rp.add_argument("--username", required=True)


def _add_role_commands(sub) -> None:
    """注册角色管理子命令组。"""
    rp = sub.add_parser("role", help="角色管理")
    r_sub = rp.add_subparsers(dest="role_action")
    r_sub.add_parser("list", help="列出所有角色")
    cp = r_sub.add_parser("create", help="创建角色")
    cp.add_argument("--code", required=True)
    cp.add_argument("--label", required=True)
    cp.add_argument("--priority", type=int, required=True)
    dp = r_sub.add_parser("delete", help="删除角色")
    dp.add_argument("--code", required=True)


def _add_quota_commands(sub) -> None:
    """注册限额管理子命令组。"""
    qp = sub.add_parser("quota", help="限额管理")
    q_sub = qp.add_subparsers(dest="quota_action")
    lp = q_sub.add_parser("list", help="查看限额")
    lp.add_argument("--account", required=True)
    sp = q_sub.add_parser("set", help="设置限额")
    sp.add_argument("--account", required=True)
    sp.add_argument("--key", required=True)
    sp.add_argument("--value", type=int, required=True)


def _add_config_commands(sub) -> None:
    """注册配置管理子命令组。"""
    cfp = sub.add_parser("config", help="系统配置")
    cf_sub = cfp.add_subparsers(dest="config_action")
    gp = cf_sub.add_parser("get", help="读取配置")
    gp.add_argument("key")
    sp = cf_sub.add_parser("set", help="设置配置")
    sp.add_argument("key")
    sp.add_argument("value")


def _add_reserved_commands(sub) -> None:
    """注册保留名管理子命令组。"""
    rvp = sub.add_parser("reserved-name", help="保留名管理")
    rv_sub = rvp.add_subparsers(dest="reserved_action")
    rv_sub.add_parser("list", help="列出保留名")
    ap = rv_sub.add_parser("add", help="添加保留名")
    ap.add_argument("name")
