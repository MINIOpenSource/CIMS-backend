"""账户创建服务。

Slug 可选，留空时自动随机生成。
"""

import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.account_member import AccountMember
from app.models.account_quota import AccountQuota

# 默认限额
_DEFAULT_QUOTAS = [
    ("max_clients", 50),
    ("max_bandwidth_mb", 1024),
    ("feature.ota", 1),
    ("feature.audit", 1),
]


async def create_account(
    name: str,
    user_id: str,
    db: AsyncSession,
    slug: Optional[str] = None,
) -> Account:
    """创建新账户并绑定 owner。slug 可选，留空自动生成。"""
    now = datetime.now(timezone.utc)
    if not slug:
        slug = f"org-{secrets.token_hex(4)}"
    account = Account(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        api_key=secrets.token_urlsafe(32),
        is_active=True,
        created_at=now,
    )
    db.add(account)
    db.add(
        AccountMember(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account.id,
            role_in_account="owner",
            joined_at=now,
        )
    )
    for key, val in _DEFAULT_QUOTAS:
        db.add(
            AccountQuota(
                id=str(uuid.uuid4()),
                account_id=account.id,
                quota_key=key,
                max_value=val,
            )
        )
    await db.commit()
    return account
