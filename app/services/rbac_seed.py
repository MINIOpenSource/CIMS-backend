"""RBAC 种子数据。

在 OOBE 或 Schema 初始化时创建默认角色和权限定义。
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_role import CustomRole
from app.models.permission_def import PermissionDef
from app.models.role_permission import RolePermission

logger = logging.getLogger(__name__)

# 默认角色（code, label, priority, is_system）
_DEFAULT_ROLES = [
    ("owner", "所有者", 100, True),
    ("admin", "管理员", 80, True),
    ("teacher", "教师", 50, True),
    ("viewer", "只读成员", 10, True),
]

# 默认权限（code, label, category）
_DEFAULT_PERMISSIONS = [
    ("client.read", "查看客户端", "client"),
    ("client.manage", "管理客户端", "client"),
    ("command.execute", "执行命令", "command"),
    ("config.edit", "编辑配置", "config"),
    ("role.manage", "管理角色", "role"),
    ("user.manage", "管理用户", "user"),
    ("audit.read", "查看审计日志", "audit"),
    ("pairing.manage", "管理配对码", "pairing"),
    ("pre_reg.manage", "管理预注册客户端", "pre_reg"),
    ("account.slug.edit", "修改账户 Slug", "account"),
]

# 角色-权限映射
_ROLE_PERMS = {
    "admin": [
        "client.read",
        "client.manage",
        "command.execute",
        "config.edit",
        "user.manage",
        "audit.read",
        "pairing.manage",
        "pre_reg.manage",
        "account.slug.edit",
    ],
    "teacher": [
        "client.read",
        "command.execute",
        "config.edit",
    ],
    "viewer": [
        "client.read",
    ],
}


async def seed_rbac(db: AsyncSession) -> None:
    """写入默认角色、权限和关联记录（幂等）。"""
    # 种子角色
    for code, label, priority, is_sys in _DEFAULT_ROLES:
        exists = (
            await db.execute(select(CustomRole).where(CustomRole.code == code))
        ).scalar_one_or_none()
        if not exists:
            db.add(
                CustomRole(
                    code=code,
                    label=label,
                    priority=priority,
                    is_system=is_sys,
                )
            )
            logger.info("创建默认角色: %s", code)

    # 种子权限
    for code, label, category in _DEFAULT_PERMISSIONS:
        exists = (
            await db.execute(select(PermissionDef).where(PermissionDef.code == code))
        ).scalar_one_or_none()
        if not exists:
            db.add(
                PermissionDef(
                    code=code,
                    label=label,
                    category=category,
                )
            )
            logger.info("创建默认权限: %s", code)

    # 种子角色-权限关联
    for role_code, perm_codes in _ROLE_PERMS.items():
        for perm_code in perm_codes:
            exists = (
                await db.execute(
                    select(RolePermission)
                    .where(RolePermission.role_code == role_code)
                    .where(RolePermission.permission_code == perm_code)
                )
            ).scalar_one_or_none()
            if not exists:
                db.add(
                    RolePermission(
                        role_code=role_code,
                        permission_code=perm_code,
                    )
                )

    await db.commit()
    logger.info("RBAC 种子数据初始化完成")
