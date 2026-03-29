"""角色分级管理服务 — 查询与创建。

提供角色列表查询和自定义角色创建。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_role import CustomRole


async def list_roles(db: AsyncSession) -> list[CustomRole]:
    """查询所有角色，按优先级降序排列。"""
    result = await db.execute(select(CustomRole).order_by(CustomRole.priority.desc()))
    return list(result.scalars().all())


async def create_role(
    code: str, label: str, priority: int, db: AsyncSession
) -> CustomRole:
    """创建自定义角色。"""
    role = CustomRole(code=code, label=label, priority=priority, is_system=False)
    db.add(role)
    await db.commit()
    return role
