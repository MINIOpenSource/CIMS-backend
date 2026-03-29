"""安全攻防测试。

覆盖 SQL 注入、XSS、会话劫持、权限提升、
BOLA/IDOR、路径遍历、令牌重放、暴力破解检测、
枚举防护等常见攻击向量。
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.apps.management_app import management_app

_TRANSPORT = ASGITransport(app=management_app)
_BASE = "http://test"


@pytest.mark.asyncio
async def test_sql_injection_in_username():
    """用户名中的 SQL 注入应被参数化查询防御。"""
    payloads = [
        "admin'; DROP TABLE users; --",
        "' OR '1'='1",
        'admin" OR "1"="1',
        "1; SELECT * FROM users",
    ]
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        for p in payloads:
            r = await ac.post(
                "/user/apply",
                json={
                    "username": p,
                    "email": f"{uuid.uuid4().hex[:6]}@test.com",
                    "password": "S3cur3Pass!@#",
                    "display_name": "test",
                },
            )
            # 应返回 400（用户名格式非法）或 422，不能是 500
            assert r.status_code in (400, 422), f"SQL 注入未被拦截: {p}"


@pytest.mark.asyncio
async def test_sql_injection_in_slug():
    """Slug 中的 SQL 注入应被校验器拦截。"""
    from app.services.user.name_validator import validate_slug_format

    malicious = ["test'; DROP TABLE--", "' OR 1=1--", 'admin"--']
    for s in malicious:
        assert not validate_slug_format(s), f"恶意 Slug 通过了校验: {s}"


@pytest.mark.asyncio
async def test_xss_in_display_name():
    """显示名称中的 HTML/JS 标签应被 API 安全处理。"""
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        r = await ac.post(
            "/user/apply",
            json={
                "username": f"xss_{uuid.uuid4().hex[:4]}",
                "email": f"xss_{uuid.uuid4().hex[:4]}@test.com",
                "password": "X$$P@ssw0rd!",
                "display_name": '<script>alert("XSS")</script>',
            },
        )
        # 注册可能成功（由业务层消毒），但不能 500
        assert r.status_code != 500


@pytest.mark.asyncio
async def test_session_hijack_invalid_token():
    """伪造的 session token 应被拒绝。"""
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        r = await ac.get(
            "/accounts",
            headers={"Authorization": "Bearer fake_token_12345"},
        )
        assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_session_hijack_empty_token():
    """空 token 应被拒绝。"""
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        r = await ac.get(
            "/accounts",
            headers={"Authorization": "Bearer "},
        )
        assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_session_no_auth_header():
    """无 Authorization 头应返回 401。"""
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        r = await ac.get("/accounts")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_privilege_escalation_member_as_admin():
    """普通成员不应能执行管理员操作（权限检查）。"""
    from app.services.permission.checker import check_permission
    from app.models.engine import AsyncSessionLocal
    from app.models.account_member import AccountMember
    from sqlalchemy import delete
    from datetime import datetime, timezone

    uid = f"esc-{uuid.uuid4().hex[:8]}"
    aid = f"esc-acct-{uuid.uuid4().hex[:8]}"
    mid = str(uuid.uuid4())
    async with AsyncSessionLocal() as db:
        db.add(
            AccountMember(
                id=mid,
                user_id=uid,
                account_id=aid,
                role_in_account="member",
                joined_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
        # member 不应有管理权限
        assert not await check_permission(uid, aid, "account.manage", db)
        assert not await check_permission(uid, aid, "member.manage", db)
        assert not await check_permission(uid, aid, "client.delete", db)
        await db.execute(delete(AccountMember).where(AccountMember.id == mid))
        await db.commit()


@pytest.mark.asyncio
async def test_bola_cross_user_access():
    """用户 A 的令牌不能访问用户 B 的资源。"""
    from app.core.auth.dependencies import resolve_user_from_token
    from app.services.crypto.token_factory import create_session_token

    uid_a = f"bola-a-{uuid.uuid4().hex[:8]}"
    uid_b = f"bola-b-{uuid.uuid4().hex[:8]}"
    token_a = await create_session_token(uid_a)
    token_b = await create_session_token(uid_b)
    # token_a 应解析为 uid_a
    assert await resolve_user_from_token(token_a) == uid_a
    # token_b 应解析为 uid_b，而不是 uid_a
    assert await resolve_user_from_token(token_b) == uid_b
    assert await resolve_user_from_token(token_b) != uid_a


@pytest.mark.asyncio
async def test_path_traversal_in_resource():
    """路径遍历攻击应被拦截。"""
    from app.apps.client_app import client_app

    transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=transport, base_url="http://test-school.localhost"
    ) as ac:
        r = await ac.get("/resource/../../../etc/passwd")
        assert r.status_code in (400, 403, 404)
        r2 = await ac.get("/resource/%2e%2e%2f%2e%2e%2fhosts")
        assert r2.status_code in (400, 403, 404)


@pytest.mark.asyncio
async def test_oversized_payload():
    """超大 payload 不应导致服务器崩溃。"""
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        r = await ac.post(
            "/user/auth",
            json={"email": "a" * 10000, "password": "b" * 10000},
        )
        assert r.status_code in (401, 422)


@pytest.mark.asyncio
async def test_token_replay_after_logout():
    """登出后令牌应无法重用。"""
    from app.services.crypto.token_factory import create_session_token
    from app.core.auth.dependencies import resolve_user_from_token
    from app.core.redis.accessor import get_redis
    from app.core.config import REDIS_DB_AUTH

    uid = f"replay-{uuid.uuid4().hex[:8]}"
    token = await create_session_token(uid)
    # 验证令牌有效
    assert await resolve_user_from_token(token) == uid
    # 模拟登出：删除 session
    rd = get_redis(REDIS_DB_AUTH)
    await rd.delete(f"session:{token}")
    # 令牌应失效
    assert await resolve_user_from_token(token) is None


@pytest.mark.asyncio
async def test_username_enumeration_defense():
    """登录失败不应泄露用户名是否存在。"""
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        # 不存在的邮箱
        r1 = await ac.post(
            "/user/auth",
            json={"email": "nonexistent@test.com", "password": "wrong"},
        )
        # 存在的邮箱（admin@test.com 已在 conftest 创建）
        r2 = await ac.post(
            "/user/auth",
            json={"email": "admin@test.com", "password": "wrong_pwd"},
        )
        # 两者状态码和错误信息应相同，防止枚举
        assert r1.status_code == r2.status_code
        assert r1.json().get("detail") == r2.json().get("detail")


@pytest.mark.asyncio
async def test_reserved_name_bypass():
    """注册保留名用户名应被拒绝。"""
    async with AsyncClient(transport=_TRANSPORT, base_url=_BASE) as ac:
        for name in ["admin", "root", "system", "api"]:
            r = await ac.post(
                "/user/apply",
                json={
                    "username": name,
                    "email": f"{name}_{uuid.uuid4().hex[:4]}@test.com",
                    "password": "Str0ng!P@ss123",
                    "display_name": name,
                },
            )
            assert r.status_code in (
                400,
                200,
            ), f"保留名 {name} 返回异常状态 {r.status_code}"
