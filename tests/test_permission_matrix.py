"""全权限矩阵测试。

验证 owner/admin/member/viewer × 9 权限组合的正确性。
"""

import pytest
import uuid
from datetime import datetime, timezone
from app.models.engine import AsyncSessionLocal
from app.models.account_member import AccountMember
from app.services.permission.checker import check_permission
from sqlalchemy import delete

# 9 个权限码
_PERMS = [
    "client.read",
    "client.write",
    "client.delete",
    "command.execute",
    "config.read",
    "config.write",
    "audit.read",
    "account.manage",
    "member.manage",
]

# 角色默认权限期望值
_ROLE_MATRIX = {
    "owner": {p: True for p in _PERMS},
    "admin": {
        "client.read": True,
        "client.write": True,
        "client.delete": True,
        "command.execute": True,
        "config.read": True,
        "config.write": True,
        "audit.read": True,
        "account.manage": False,
        "member.manage": True,
    },
    "member": {
        "client.read": True,
        "client.write": True,
        "client.delete": False,
        "command.execute": True,
        "config.read": True,
        "config.write": False,
        "audit.read": False,
        "account.manage": False,
        "member.manage": False,
    },
    "viewer": {
        "client.read": True,
        "client.write": False,
        "client.delete": False,
        "command.execute": False,
        "config.read": True,
        "config.write": False,
        "audit.read": False,
        "account.manage": False,
        "member.manage": False,
    },
}


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["owner", "admin", "member", "viewer"])
async def test_role_permission_matrix(role):
    """验证角色默认权限矩阵。"""
    uid = f"matrix-{role}-{uuid.uuid4().hex[:6]}"
    aid = f"matrix-acct-{uuid.uuid4().hex[:6]}"
    mid = str(uuid.uuid4())
    async with AsyncSessionLocal() as db:
        db.add(
            AccountMember(
                id=mid,
                user_id=uid,
                account_id=aid,
                role_in_account=role,
                joined_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
        expected = _ROLE_MATRIX[role]
        for perm, should_have in expected.items():
            result = await check_permission(uid, aid, perm, db)
            assert result == should_have, (
                f"{role} 应{'有' if should_have else '无'} "
                f"{perm}，但结果为 {result}"
            )
        # 清理
        await db.execute(delete(AccountMember).where(AccountMember.id == mid))
        await db.commit()


@pytest.mark.asyncio
async def test_no_membership_has_no_permissions():
    """用户不属于任何账户时，应无任何权限。"""
    uid = f"orphan-{uuid.uuid4().hex[:8]}"
    aid = f"orphan-acct-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        for perm in _PERMS:
            assert not await check_permission(uid, aid, perm, db)
