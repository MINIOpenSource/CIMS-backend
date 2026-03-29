"""共享测试夹具 - 初始化 PG、Redis 和默认测试账户。"""

import os
import warnings
from datetime import datetime, timezone
from pathlib import Path

# 在导入任何依赖 imghdr 的模块之前抑制此弃用警告
warnings.filterwarnings(
    "ignore", message="imghdr was removed", category=DeprecationWarning
)

import pytest_asyncio  # noqa: E402

# 加载 .env 文件（确保测试使用真实配置）
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# 仅在 .env 未提供时使用回退默认值
os.environ.setdefault("CIMS_KEY_FILE", "/tmp/test_cims_server.key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:password@localhost:5432/cims",
)
os.environ.setdefault("REDIS_URL", "redis://:password@localhost:6379/0")
os.environ["CIMS_BASE_DOMAIN"] = "localhost"

from app.core.redis import init_redis  # noqa: E402
from app.models.database import init_db, AsyncSessionLocal, Account  # noqa: E402
from app.models.database import ensure_tenant_schema  # noqa: E402
from app.core.tenant import tenant_ctx, schema_ctx  # noqa: E402

TEST_ACCOUNT_ID = "test-account-00000000"
TEST_ACCOUNT_SLUG = "test-school"
TEST_ACCOUNT_NAME = "Test School"
TEST_SCHEMA = f"tenant_{TEST_ACCOUNT_SLUG}"

# 向后兼容别名（供旧测试文件使用）
TEST_TENANT_ID = TEST_ACCOUNT_ID
TEST_TENANT_SLUG = TEST_ACCOUNT_SLUG
TEST_TENANT_NAME = TEST_ACCOUNT_NAME


@pytest_asyncio.fixture(autouse=True)
async def setup_infra():
    """初始化 PG 表、Redis、确保测试账户存在并设置 ContextVar。"""
    await init_redis()
    await init_db()
    await ensure_tenant_schema(TEST_ACCOUNT_SLUG)
    # 确保测试账户存在
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(Account).where(Account.id == TEST_ACCOUNT_ID))
        if result.scalar_one_or_none() is None:
            db.add(
                Account(
                    id=TEST_ACCOUNT_ID,
                    name=TEST_ACCOUNT_NAME,
                    slug=TEST_ACCOUNT_SLUG,
                    api_key="test-api-key",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
    t_token = tenant_ctx.set(TEST_ACCOUNT_ID)
    s_token = schema_ctx.set(TEST_SCHEMA)
    yield TEST_ACCOUNT_ID
    schema_ctx.reset(s_token)
    tenant_ctx.reset(t_token)


@pytest_asyncio.fixture()
async def test_account(setup_infra):
    """兼容别名：返回测试账户 ID。"""
    return setup_infra


@pytest_asyncio.fixture()
async def admin_token():
    """生成用于测试的管理员会话令牌。"""
    from app.services.crypto.token_factory import create_session_token

    # 创建测试超管用户
    user_id = "test-superadmin-user"
    return await create_session_token(user_id)


@pytest_asyncio.fixture()
async def admin_headers(admin_token):
    """便捷夹具：管理端请求的认证头。"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture()
async def test_superadmin_user():
    """确保测试超管用户存在并返回其信息。"""
    from app.models.user import User
    from app.services.crypto.hasher import hash_password
    from sqlalchemy import select

    user_id = "test-superadmin-user"
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        if result.scalar_one_or_none() is None:
            db.add(
                User(
                    id=user_id,
                    username="test_superadmin",
                    email="admin@test.com",
                    hashed_password=hash_password("TestPassword123!"),
                    display_name="测试超管",
                    role_code="superadmin",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
    return user_id


@pytest_asyncio.fixture()
async def command_headers():
    """生成旧式 command 令牌头（向后兼容）。"""
    from app.services.auth_token import generate_token

    token = await generate_token("command", tenant_id=TEST_ACCOUNT_ID)
    return {"Authorization": f"Bearer {token}"}
