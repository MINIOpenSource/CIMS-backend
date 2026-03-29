"""RBAC 权限检查依赖。

提供 FastAPI 依赖函数，实现路由级的细粒度权限控制。
"""

import logging

from fastapi import Request, HTTPException
from sqlalchemy import select

from app.models.database import AsyncSessionLocal
from app.models.account_member import AccountMember
from app.models.role_permission import RolePermission
from app.models.member_permission import MemberPermission
from app.core.tenant.context import get_tenant_id, set_search_path

logger = logging.getLogger(__name__)


async def _get_member_permissions(user_id: str, account_id: str) -> set[str]:
    """汇总用户在指定账户内的有效权限集合。"""
    async with AsyncSessionLocal() as db:
        await set_search_path(db)
        # 查询成员关系
        stmt = (
            select(AccountMember)
            .where(AccountMember.user_id == user_id)
            .where(AccountMember.account_id == account_id)
        )
        member = (await db.execute(stmt)).scalar_one_or_none()
        if not member:
            return set()

        # owner 拥有所有权限
        if member.role_in_account == "owner":
            return {"*"}

        # 角色权限
        role_perms_stmt = select(RolePermission.permission_code).where(
            RolePermission.role_code == member.role_in_account
        )
        role_perms = set((await db.execute(role_perms_stmt)).scalars().all())

        # 成员级覆盖
        member_overrides_stmt = select(MemberPermission).where(
            MemberPermission.member_id == member.id
        )
        overrides = (await db.execute(member_overrides_stmt)).scalars().all()
        for ov in overrides:
            if ov.granted:
                role_perms.add(ov.permission_code)
            else:
                role_perms.discard(ov.permission_code)

        return role_perms


def require_permission(*perms: str):
    """返回一个 FastAPI 依赖，检查当前用户是否拥有所有指定权限。"""

    async def _checker(request: Request):
        """权限检查依赖实现。"""
        user_id = getattr(request.state, "current_user_id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="未认证")
        account_id = get_tenant_id()
        if not account_id:
            raise HTTPException(status_code=403, detail="租户上下文缺失")
        granted = await _get_member_permissions(user_id, account_id)
        # owner 拥有所有权限
        if "*" in granted:
            return user_id
        for p in perms:
            if p not in granted:
                logger.warning("权限不足: user=%s perm=%s", user_id, p)
                raise HTTPException(status_code=403, detail=f"缺少权限: {p}")
        return user_id

    return _checker
