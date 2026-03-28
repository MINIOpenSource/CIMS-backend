import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.apps.client_app import client_app
from app.apps.management_app import management_app

from tests.conftest import TEST_TENANT_ID, TEST_ACCOUNT_ID


@pytest_asyncio.fixture(autouse=True)
async def register_test_client_online():
    """注册一个模拟 gRPC 客户端为在线状态（IP 127.0.0.1）。"""
    from app.core.redis import get_redis
    from app.core.config import REDIS_DB_SESSION

    rd = get_redis(REDIS_DB_SESSION)
    key = f"online:{TEST_TENANT_ID}:test-grpc-client"
    await rd.hset(key, mapping={"status": "online", "ip": "127.0.0.1"})
    await rd.expire(key, 300)
    yield
    await rd.delete(key)


@pytest_asyncio.fixture(autouse=True)
async def lifespan():
    async with client_app.router.lifespan_context(client_app):
        # Share state with management_app
        management_app.state.command_servicer = getattr(
            client_app.state, "command_servicer", None
        )
        management_app.state.session_manager = getattr(
            client_app.state, "session_manager", None
        )
        yield


# ---- 路径前缀常量 ----
_RES_PREFIX = f"/account/{TEST_ACCOUNT_ID}"


@pytest.mark.asyncio
async def test_read_main():
    transport = ASGITransport(app=client_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "CIMS Backend is running"}


@pytest.mark.asyncio
async def test_get_client_manifest():
    transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=transport, base_url="http://test-school.localhost"
    ) as ac:
        response = await ac.get("/api/v1/client/test-uuid/manifest")
    assert response.status_code == 200
    data = response.json()
    assert "ClassPlanSource" in data
    assert "default_classplan" in data["ClassPlanSource"]["Value"]
    assert data["ServerKind"] == 1


@pytest.mark.asyncio
async def test_command_endpoints(command_headers):
    transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        # Create a ClassPlan
        create_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/create?name=test_cp",
            headers=command_headers,
        )
        assert create_res.status_code == 200
        assert create_res.json()["status"] == "success"

        # List it
        list_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/list", headers=command_headers
        )
        assert list_res.status_code == 200
        assert "test_cp" in list_res.json()

        # Delete it
        del_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/delete?name=test_cp",
            headers=command_headers,
        )
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"

        # Create again for write tests
        await ac.get(
            f"{_RES_PREFIX}/ClassPlan/create?name=test_cp2",
            headers=command_headers,
        )

        # Write
        write_res = await ac.put(
            f"{_RES_PREFIX}/ClassPlan/write?name=test_cp2",
            json={"nested": {"value": 1}, "preserve": True},
            headers=command_headers,
        )
        assert write_res.status_code == 200

        # Deep Merge Update
        patch_res = await ac.patch(
            f"{_RES_PREFIX}/ClassPlan/update?name=test_cp2",
            json={"nested": {"value": 2}, "new_key": "exists"},
            headers=command_headers,
        )
        assert patch_res.status_code == 200

        # Validate via token endpoint
        token_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/token?name=test_cp2",
            headers=command_headers,
        )
        assert token_res.status_code == 200
        token_url = token_res.json()["url"]

        # Fetch via client app
        client_transport = ASGITransport(app=client_app)
        async with AsyncClient(
            transport=client_transport, base_url="http://test-school.localhost"
        ) as cc:
            data_res = await cc.get(token_url)
            assert data_res.status_code == 200
            data = data_res.json()
            assert data["nested"]["value"] == 2
            assert data["preserve"] is True
            assert data["new_key"] == "exists"

        # Batch test
        batch_payload = {
            "operations": [
                {
                    "action": "create",
                    "resource_type": "TimeLayout",
                    "name": "test_batch_layout",
                    "payload": {},
                },
                {
                    "action": "delete",
                    "resource_type": "ClassPlan",
                    "name": "test_cp2",
                },
            ]
        }
        batch_res = await ac.post(
            f"{_RES_PREFIX}/batch",
            json=batch_payload,
            headers=command_headers,
        )
        assert batch_res.status_code == 200
        assert batch_res.json()["status"] == "success"

        list_tl = await ac.get(
            f"{_RES_PREFIX}/TimeLayout/list", headers=command_headers
        )
        assert "test_batch_layout" in list_tl.json()

        list_cp = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/list", headers=command_headers
        )
        assert "test_cp2" not in list_cp.json()


@pytest.mark.asyncio
async def test_get_client_manifest_with_profile():
    from app.models.database import AsyncSessionLocal, ClientProfile
    import datetime
    import uuid

    test_uuid = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        from app.core.tenant.context import set_search_path

        await set_search_path(session)
        new_profile = ClientProfile(
            client_id=test_uuid,
            class_plan="my_cp",
            time_layout="my_tl",
            subjects="my_sub",
            default_settings="my_set",
            policy="my_pol",
            components="my_comp",
            credentials="my_cred",
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add(new_profile)
        await session.commit()

    transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=transport, base_url="http://test-school.localhost"
    ) as ac:
        response = await ac.get(f"/api/v1/client/{test_uuid}/manifest")
    assert response.status_code == 200
    data = response.json()
    assert "my_cp" in data["ClassPlanSource"]["Value"]
    assert "my_tl" in data["TimeLayoutSource"]["Value"]
    assert "my_comp" in data["ComponentsSource"]["Value"]


@pytest.mark.asyncio
async def test_get_client_resource():
    import uuid

    test_uid = str(uuid.uuid4())

    transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=transport, base_url="http://test-school.localhost"
    ) as cc:
        # Invalid resource type
        res = await cc.get("/api/v1/client/InvalidRes?name=test")
        assert res.status_code == 400

    # Need command token for management_app command endpoints
    from app.services.auth_token import generate_token

    cmd_token = await generate_token("command", tenant_id=TEST_TENANT_ID)
    cmd_headers = {"Authorization": f"Bearer {cmd_token}"}

    mgr_transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=mgr_transport, base_url="http://test"
    ) as ac:
        # Create and write
        await ac.get(
            f"{_RES_PREFIX}/ClassPlan/create?name=valid_cp_{test_uid}",
            headers=cmd_headers,
        )
        await ac.put(
            f"{_RES_PREFIX}/ClassPlan/write?name=valid_cp_{test_uid}",
            json={"valid": True},
            headers=cmd_headers,
        )

        # Get token
        token_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/token?name=valid_cp_{test_uid}",
            headers=cmd_headers,
        )
        assert token_res.status_code == 200
        token_url = token_res.json()["url"]

    # Use the token on the client app
    async with AsyncClient(
        transport=transport, base_url="http://test-school.localhost"
    ) as cc:
        res = await cc.get(token_url)
        assert res.status_code == 200
        assert res.json() == {"valid": True}

        # Token is single-use — reusing should fail
        res = await cc.get(token_url)
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_endpoint_invalid_token():
    transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=transport, base_url="http://test-school.localhost"
    ) as ac:
        res = await ac.get("/get?token=totally_invalid_token")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_endpoint_corrupted_resource():
    import uuid
    from app.models.database import AsyncSessionLocal, CPFile
    import datetime

    test_uid = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        from app.core.tenant.context import set_search_path

        await set_search_path(session)
        session.add(
            CPFile(
                name=f"corrupted_cp_{test_uid}",
                content="{invalid_json:",
                version=1,
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
        )
        await session.commit()

    from app.services.auth_token import generate_token

    cmd_token = await generate_token("command", tenant_id=TEST_TENANT_ID)
    cmd_headers = {"Authorization": f"Bearer {cmd_token}"}

    mgr_transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=mgr_transport, base_url="http://test"
    ) as ac:
        token_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/token?name=corrupted_cp_{test_uid}",
            headers=cmd_headers,
        )
        assert token_res.status_code == 200
        token_url = token_res.json()["url"]

    client_transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=client_transport, base_url="http://test-school.localhost"
    ) as cc:
        res = await cc.get(token_url)
        assert res.status_code == 500


@pytest.mark.asyncio
async def test_command_token_endpoint():
    import uuid

    test_uid = str(uuid.uuid4())

    from app.services.auth_token import generate_token

    cmd_token = await generate_token("command", tenant_id=TEST_TENANT_ID)
    cmd_headers = {"Authorization": f"Bearer {cmd_token}"}

    mgr_transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=mgr_transport, base_url="http://test"
    ) as ac:
        # Invalid resource type
        res = await ac.get(
            f"{_RES_PREFIX}/InvalidRes/token?name=test",
            headers=cmd_headers,
        )
        assert res.json()["status"] == "error"

        # Non-existent resource
        res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/token?name=nonexist_{test_uid}",
            headers=cmd_headers,
        )
        assert res.json()["status"] == "error"

        # Valid resource — get token and use it
        await ac.get(
            f"{_RES_PREFIX}/ClassPlan/create?name=token_cp_{test_uid}",
            headers=cmd_headers,
        )
        await ac.put(
            f"{_RES_PREFIX}/ClassPlan/write?name=token_cp_{test_uid}",
            json={"hello": "world"},
            headers=cmd_headers,
        )

        token_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/token?name=token_cp_{test_uid}",
            headers=cmd_headers,
        )
        assert token_res.status_code == 200
        data = token_res.json()
        assert "token" in data
        assert data["url"].startswith("/get?token=")

    # Use the token on client app
    client_transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=client_transport, base_url="http://test-school.localhost"
    ) as cc:
        get_res = await cc.get(data["url"])
        assert get_res.status_code == 200
        assert get_res.json() == {"hello": "world"}


# ---------------------------------------------------------------------------
# IP Authentication Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_ip_auth_pass():
    """当请求 IP 匹配在线 gRPC 客户端时，返回真实数据。"""
    import uuid

    test_uid = str(uuid.uuid4())

    from app.services.auth_token import generate_token

    cmd_token = await generate_token("command", tenant_id=TEST_TENANT_ID)
    cmd_headers = {"Authorization": f"Bearer {cmd_token}"}

    mgr_transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=mgr_transport, base_url="http://test"
    ) as ac:
        await ac.get(
            f"{_RES_PREFIX}/ClassPlan/create?name=ip_pass_{test_uid}",
            headers=cmd_headers,
        )
        await ac.put(
            f"{_RES_PREFIX}/ClassPlan/write?name=ip_pass_{test_uid}",
            json={"ip_test": "pass"},
            headers=cmd_headers,
        )
        token_res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/token?name=ip_pass_{test_uid}",
            headers=cmd_headers,
        )
        token_url = token_res.json()["url"]

    # 127.0.0.1 is online (from fixture), httpx sends from 127.0.0.1 → should pass
    client_transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=client_transport, base_url="http://test-school.localhost"
    ) as cc:
        res = await cc.get(token_url)
        assert res.status_code == 200
        assert res.json() == {"ip_test": "pass"}


@pytest.mark.asyncio
async def test_get_ip_auth_fail():
    """当请求 IP 不匹配任何在线 gRPC 客户端时，返回空对象。"""
    import uuid

    test_uid = str(uuid.uuid4())

    from app.services.auth_token import generate_token

    cmd_token = await generate_token("command", tenant_id=TEST_TENANT_ID)
    cmd_headers = {"Authorization": f"Bearer {cmd_token}"}

    mgr_transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=mgr_transport, base_url="http://test"
    ) as ac:
        await ac.get(
            f"{_RES_PREFIX}/ClassPlan/create?name=ip_fail_{test_uid}",
            headers=cmd_headers,
        )
        await ac.put(
            f"{_RES_PREFIX}/ClassPlan/write?name=ip_fail_{test_uid}",
            json={"ip_test": "should_not_see"},
            headers=cmd_headers,
        )

    # Remove the online entry so no IPs match
    from app.core.redis import get_redis
    from app.core.config import REDIS_DB_SESSION

    rd = get_redis(REDIS_DB_SESSION)
    await rd.delete(f"online:{TEST_TENANT_ID}:test-grpc-client")

    # Create a fresh token directly
    from app.services.resource_token import create_token

    token = await create_token(
        TEST_TENANT_ID, "ClassPlan", f"ip_fail_{test_uid}", client_ip="127.0.0.1"
    )

    client_transport = ASGITransport(app=client_app)
    async with AsyncClient(
        transport=client_transport, base_url="http://test-school.localhost"
    ) as cc:
        res = await cc.get(f"/get?token={token}")
        assert res.status_code == 200
        assert res.json() == {}


@pytest.mark.asyncio
async def test_parse_grpc_peer_ip():
    """测试各种格式下的 gRPC 对端 IP 解析器。"""
    from app.grpc.session_manager import parse_grpc_peer_ip

    assert parse_grpc_peer_ip("ipv4:192.168.1.1:50051") == "192.168.1.1"
    assert parse_grpc_peer_ip("ipv6:[::1]:50051") == "::1"
    assert parse_grpc_peer_ip("ipv6:[2001:db8::1]:443") == "2001:db8::1"
    assert parse_grpc_peer_ip("") == ""
    assert parse_grpc_peer_ip("some-raw-peer") == "some-raw-peer"


# ---------------------------------------------------------------------------
# Token Auth Middleware Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_command_without_token():
    """命令端点拒绝未携带 Bearer Token 的请求。"""
    transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        res = await ac.get(f"{_RES_PREFIX}/ClassPlan/list")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_command_with_invalid_token():
    """命令端点拒绝携带无效令牌的请求。"""
    transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        res = await ac.get(
            f"{_RES_PREFIX}/ClassPlan/list",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_login_and_use(test_superadmin_user):
    """测试完整的管理端登录流程：登录 → 使用令牌 → 登出。"""
    transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        # 使用邮箱/密码登录
        login_res = await ac.post(
            "/user/auth",
            json={"email": "admin@test.com", "password": "TestPassword123!"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["token"]

        # 使用令牌访问
        headers = {"Authorization": f"Bearer {token}"}
        logout_res = await ac.post("/token/deactivate", headers=headers)
        assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_admin_login_bad_password(test_superadmin_user):
    """管理端登录拒绝错误密码。"""
    transport = ASGITransport(app=management_app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        res = await ac.post(
            "/user/auth",
            json={"email": "admin@test.com", "password": "WrongPass!"},
        )
        assert res.status_code == 401
