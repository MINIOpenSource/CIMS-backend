"""OOBE 初始化执行器。

将配置写入 .cims/config.json，连接数据库，
创建所有表，初始化超级管理员用户和默认数据。
"""

import json
import uuid
import secrets
from datetime import datetime, timezone
from pathlib import Path

from .detector import CONFIG_DIR, CONFIG_FILE


def write_config_file(config: dict) -> None:
    """将数据库连接信息写入 .cims/config.json。"""
    CONFIG_DIR.mkdir(exist_ok=True)
    file_config = {"database_url": config["db_url"]}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(file_config, f, indent=2, ensure_ascii=False)
    print(f"✅ 配置已写入 {CONFIG_FILE}")


async def init_database(config: dict) -> None:
    """连接数据库并执行完整初始化。"""
    # 动态设置数据库 URL
    import app.core.config as cfg

    cfg.DATABASE_URL = config["db_url"]
    # 重建引擎
    from app.models.engine import engine
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表已创建")
    # 写入系统配置到数据库
    await _init_system_config(config)
    # 创建默认数据
    await _init_default_data(config)
    print("✅ 初始化完成")


async def _init_system_config(config: dict) -> None:
    """将非数据库连接的配置写入 system_config 表。"""
    from app.models.engine import AsyncSessionLocal
    from app.models.system_config import SystemConfig

    now = datetime.now(timezone.utc)
    entries = [
        ("redis_url", config["redis_url"]),
        ("base_domain", config["domain"]),
        ("oobe_completed", "true"),
    ]
    async with AsyncSessionLocal() as db:
        for key, val in entries:
            db.add(SystemConfig(key=key, value=val, updated_at=now))
        await db.commit()


async def _init_default_data(config: dict) -> None:
    """创建超管用户、默认角色、权限定义和保留名。"""
    from app.models.engine import AsyncSessionLocal
    from app.services.user.role_init import ensure_system_roles

    async with AsyncSessionLocal() as db:
        await ensure_system_roles(db)
        await _create_superadmin(config, db)
        await _init_permissions(db)
        await _init_reserved_names(db)


async def _create_superadmin(config: dict, db) -> None:
    """创建超级管理员用户和默认账户。"""
    from app.models.user import User
    from app.models.account import Account
    from app.models.account_member import AccountMember
    from app.services.crypto.hasher import hash_password

    now = datetime.now(timezone.utc)
    user = User(
        id=str(uuid.uuid4()),
        username=config["username"],
        email=config["email"],
        hashed_password=hash_password(config["password"]),
        display_name="超级管理员",
        role_code="superadmin",
        is_active=True,
        created_at=now,
    )
    db.add(user)
    account = Account(
        id=str(uuid.uuid4()),
        name="默认管理账户",
        slug=config["username"].replace("_", "-"),
        api_key=secrets.token_urlsafe(32),
        is_active=True,
        created_at=now,
    )
    db.add(account)
    db.add(
        AccountMember(
            id=str(uuid.uuid4()),
            user_id=user.id,
            account_id=account.id,
            role_in_account="owner",
            joined_at=now,
        )
    )
    await db.commit()
    print(f"✅ 超级管理员 {config['username']} 已创建")


async def _init_permissions(db) -> None:
    """初始化默认权限定义。"""
    from app.models.permission_def import PermissionDef

    perms = [
        ("client.read", "读取客户端", "client"),
        ("client.write", "修改客户端", "client"),
        ("client.delete", "删除客户端", "client"),
        ("command.execute", "执行远程命令", "command"),
        ("config.read", "读取配置", "config"),
        ("config.write", "修改配置", "config"),
        ("audit.read", "查看审计日志", "audit"),
        ("account.manage", "管理账户", "account"),
        ("member.manage", "管理成员", "member"),
    ]
    for code, label, cat in perms:
        db.add(PermissionDef(code=code, label=label, category=cat))
    await db.commit()


async def _init_reserved_names(db) -> None:
    """初始化保留名称注册表（150+ 条目）。"""
    from app.models.reserved_name import ReservedName
    from app.oobe.reserved_list import RESERVED_NAMES

    for name in RESERVED_NAMES:
        db.add(ReservedName(name=name, reason="系统保留"))
    await db.commit()


def generate_systemd_service() -> None:
    """生成 cims-backend.service 文件并尝试安装到 systemd。

    自动检测 cims 可执行文件路径和工作目录，
    生成标准 systemd unit 文件。安装失败时仅打印提示，不阻塞初始化。
    """
    import os
    import shutil
    import subprocess

    cims_bin = shutil.which("cims")
    if not cims_bin:
        # 回退到 uv run cims
        cims_bin = f"{shutil.which('uv') or 'uv'} run cims"

    work_dir = str(Path(__file__).resolve().parent.parent.parent)
    user = os.environ.get("USER", "root")

    service_content = f"""\
[Unit]
Description=CIMS Backend - ClassIsland Management Server
Documentation=https://github.com/ClassIsland/CIMS-backend
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User={user}
Group={user}
WorkingDirectory={work_dir}
ExecStart={cims_bin} daemon
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cims-backend

# 安全加固
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths={work_dir}

# 环境
EnvironmentFile=-{work_dir}/.env

[Install]
WantedBy=multi-user.target
"""

    # 写入本地副本
    local_path = CONFIG_DIR / "cims-backend.service"
    local_path.write_text(service_content, encoding="utf-8")
    print(f"✅ 服务文件已生成: {local_path}")

    # 尝试安装到 systemd
    systemd_path = "/etc/systemd/system/cims-backend.service"
    try:
        install_cmd = ["sudo", "cp", str(local_path), systemd_path]
        result = subprocess.run(install_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            subprocess.run(
                ["sudo", "systemctl", "daemon-reload"],
                capture_output=True,
                text=True,
            )
            print(f"✅ 服务已安装到 {systemd_path}")
            print("   启动: cims start")
            print("   开机自启: cims startup")
        else:
            _print_manual_install(local_path, systemd_path)
    except FileNotFoundError:
        _print_manual_install(local_path, systemd_path)


def _print_manual_install(local_path, systemd_path) -> None:
    """打印手动安装 systemd 服务的提示。

    Args:
        local_path: 本地服务文件路径。
        systemd_path: 目标 systemd 路径。
    """
    print("⚠️  无法自动安装服务文件，请手动执行:")
    print(f"   sudo cp {local_path} {systemd_path}")
    print("   sudo systemctl daemon-reload")
