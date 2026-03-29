"""角色分级管理服务 — 初始化与删除。

确保系统内置角色存在；删除自定义角色。
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_role import CustomRole

# 系统内置角色初始数据
SYSTEM_ROLES = [
    ("banned", "已封禁", -1),
    ("pending", "待激活", 0),
    ("normal", "普通用户", 10),
    ("admin", "管理员", 90),
    ("superadmin", "超级管理员", 100),
]


async def ensure_system_roles(db: AsyncSession) -> None:
    """确保系统内置角色存在（幂等操作）。"""
    for code, label, priority in SYSTEM_ROLES:
        exists = await db.execute(select(CustomRole).where(CustomRole.code == code))
        if exists.scalar_one_or_none():
            continue
        db.add(
            CustomRole(
                code=code,
                label=label,
                priority=priority,
                is_system=True,
            )
        )
    await db.commit()


async def delete_role(code: str, db: AsyncSession) -> Optional[str]:
    """删除自定义角色。系统角色不可删除。"""
    result = await db.execute(select(CustomRole).where(CustomRole.code == code))
    role = result.scalar_one_or_none()
    if not role:
        return "角色不存在"
    if role.is_system:
        return "系统内置角色不可删除"
    await db.delete(role)
    await db.commit()
    return None
