"""租户 Schema 初始化工具。

提供在 PostgreSQL 中为新租户创建独立 Schema 并建表的功能。
"""

from sqlalchemy import text
from app.models.engine import engine
from app.models.base import Base
from app.core.tenant.context import safe_identifier

# 仅在 public Schema 中存放的表（不应在租户 Schema 中重复创建）
# 仅在 public Schema 中存放的全局表
_PUBLIC_ONLY = {
    "accounts",
    "users",
    "custom_roles",
    "account_members",
    "permission_defs",
    "member_permissions",
    "role_permissions",
    "account_quotas",
    "system_config",
    "reserved_names",
    "invitations",
}


async def ensure_tenant_schema(slug: str) -> str:
    """确保指定租户的 Schema 存在，不存在则自动创建并建表。

    Args:
        slug: 租户标识（用于构造 Schema 名称）。

    Returns:
        创建或已存在的 Schema 全名。
    """
    schema_name = safe_identifier(f"tenant_{slug}")
    tenant_tables = [
        t for t in Base.metadata.sorted_tables if t.name not in _PUBLIC_ONLY
    ]
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        await conn.execute(text(f'SET search_path TO "{schema_name}"'))
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tenant_tables)
        )
        await conn.execute(text("SET search_path TO public"))
    return schema_name
