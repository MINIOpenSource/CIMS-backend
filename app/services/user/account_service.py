"""账户 slug 修改服务。

提供账户 slug 的格式校验、唯一性检查和权限验证。
"""

import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.account_member import AccountMember

# Slug 格式校验：3~64 位 [a-z0-9-]
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,62}[a-z0-9]$")


async def update_account_slug(
    account_id: str,
    new_slug: str,
    user_id: str,
    db: AsyncSession,
) -> Optional[Account]:
    """修改账户 slug（需 owner/admin 角色）。"""
    if not _SLUG_RE.match(new_slug):
        raise ValueError("Slug 格式不合法（3~64位小写字母数字连字符）")
    dup = await db.execute(
        select(Account).where(Account.slug == new_slug, Account.id != account_id)
    )
    if dup.scalar_one_or_none():
        raise ValueError("该 Slug 已被占用")
    member = await db.execute(
        select(AccountMember).where(
            AccountMember.user_id == user_id,
            AccountMember.account_id == account_id,
        )
    )
    m = member.scalar_one_or_none()
    if not m or m.role_in_account not in ("owner", "admin"):
        raise PermissionError("需要账户 owner 或 admin 角色")
    acct = await db.execute(select(Account).where(Account.id == account_id))
    account = acct.scalar_one_or_none()
    if not account:
        return None
    account.slug = new_slug
    await db.commit()
    return account
