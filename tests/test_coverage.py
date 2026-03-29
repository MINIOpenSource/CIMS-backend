import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.apps.client_app import client_app
from app.apps.management_app import management_app

from tests.conftest import TEST_TENANT_ID, TEST_ACCOUNT_ID


@pytest_asyncio.fixture(autouse=True)
async def register_test_client_online():
    """注册模拟 gRPC 客户端为在线状态（IP 127.0.0.1）以通过 IP 认证。"""
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
        management_app.state.command_servicer = getattr(
            client_app.state, "command_servicer", None
        )
        management_app.state.session_manager = getattr(
            client_app.state, "session_manager", None
        )
        yield


# ---- 路径前缀常量 ----
_CMD_PREFIX = f"/accounts/{TEST_ACCOUNT_ID}/command"


@pytest.mark.asyncio
async def test_command_edge_cases(command_headers):
    transport = ASGITransport(app=management_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        h = command_headers
        # Invalid resource type for Create
        res = await ac.get(
            f"{_CMD_PREFIX}/datas/InvalidRes/create?name=test", headers=h
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"

        # Create already existing
        await ac.get(
            f"{_CMD_PREFIX}/datas/TimeLayout/create?name=duplicate_tl", headers=h
        )
        res = await ac.get(
            f"{_CMD_PREFIX}/datas/TimeLayout/create?name=duplicate_tl", headers=h
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"

        # Invalid resource type for List
        res = await ac.get(f"{_CMD_PREFIX}/datas/InvalidRes/list", headers=h)
        assert res.status_code == 400

        # Invalid resource type for Delete
        res = await ac.delete(
            f"{_CMD_PREFIX}/datas/InvalidRes/delete?name=test", headers=h
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"

        # Delete non-existing
        res = await ac.delete(
            f"{_CMD_PREFIX}/datas/TimeLayout/delete?name=not_found", headers=h
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"

        # Invalid resource type for Write
        res = await ac.post(
            f"{_CMD_PREFIX}/datas/InvalidRes/write?name=test", json={}, headers=h
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"

        # Invalid resource type for Update
        res = await ac.patch(
            f"{_CMD_PREFIX}/datas/InvalidRes/update?name=test", json={}, headers=h
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"

        # Update non-existing
        res = await ac.patch(
            f"{_CMD_PREFIX}/datas/TimeLayout/update?name=not_found_tl",
            json={},
            headers=h,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "error"

        # Client list, status, restart
        res = await ac.get(f"{_CMD_PREFIX}/clients/list", headers=h)
        assert res.status_code == 200
        res = await ac.get(f"{_CMD_PREFIX}/clients/status", headers=h)
        assert res.status_code == 200
        res = await ac.get(f"{_CMD_PREFIX}/client/test-uid/restart", headers=h)
        assert res.status_code == 200

        # Batch operations edge cases
        batch_payload = {
            "operations": [
                {
                    "action": "create",
                    "resource_type": "InvalidRes",
                    "name": "test",
                    "payload": {},
                },
                {
                    "action": "create",
                    "resource_type": "TimeLayout",
                    "name": "duplicate_tl",
                    "payload": {},
                },
                {
                    "action": "write",
                    "resource_type": "TimeLayout",
                    "name": "new_write_tl",
                    "payload": {},
                },
                {
                    "action": "update",
                    "resource_type": "TimeLayout",
                    "name": "missing_update_tl",
                    "payload": {},
                },
                {
                    "action": "delete",
                    "resource_type": "TimeLayout",
                    "name": "missing_delete_tl",
                    "payload": None,
                },
            ]
        }
        res = await ac.post(f"{_CMD_PREFIX}/datas/batch", json=batch_payload, headers=h)
        assert res.status_code == 200

        # Successful Batch and Granular Updates
        import uuid

        uid = str(uuid.uuid4())
        valid_batch = {
            "operations": [
                {
                    "action": "create",
                    "resource_type": "TimeLayout",
                    "name": f"batch_tl_{uid}",
                    "payload": {},
                },
                {
                    "action": "write",
                    "resource_type": "TimeLayout",
                    "name": f"batch_tl_{uid}",
                    "payload": {"a": 1},
                },
                {
                    "action": "update",
                    "resource_type": "TimeLayout",
                    "name": f"batch_tl_{uid}",
                    "payload": {"b": 2},
                },
                {
                    "action": "delete",
                    "resource_type": "TimeLayout",
                    "name": f"batch_tl_{uid}",
                    "payload": None,
                },
            ]
        }
        res = await ac.post(f"{_CMD_PREFIX}/datas/batch", json=valid_batch, headers=h)
        assert res.status_code == 200
        assert all(r["status"] == "success" for r in res.json()["results"])

        # Granular write creates new
        await ac.get(
            f"{_CMD_PREFIX}/datas/ClassPlan/create?name=gran_cp_{uid}", headers=h
        )
        await ac.put(
            f"{_CMD_PREFIX}/datas/ClassPlan/write?name=gran_cp_{uid}",
            json={"test": {"old": 1}},
            headers=h,
        )
        res = await ac.patch(
            f"{_CMD_PREFIX}/datas/ClassPlan/update?name=gran_cp_{uid}",
            json={"test": {"new": 2}},
            headers=h,
        )
        assert res.status_code == 200

        # write_data with non-existent record (auto-create)
        write_new_name = f"new_write_{uid}"
        res = await ac.put(
            f"{_CMD_PREFIX}/datas/ClassPlan/write?name={write_new_name}",
            json={"new_data": True},
            headers=h,
        )
        assert res.status_code == 200

        # Granular update over corrupted JSON
        from app.models.database import AsyncSessionLocal, CPFile
        import datetime

        corrupted_name = f"corrupt_update_{uid}"
        async with AsyncSessionLocal() as session:
            session.add(
                CPFile(
                    name=corrupted_name,
                    content="{corrupted",
                    version=1,
                    updated_at=datetime.datetime.now(datetime.timezone.utc),
                )
            )
            await session.commit()

        res = await ac.patch(
            f"{_CMD_PREFIX}/datas/ClassPlan/update?name={corrupted_name}",
            json={"valid": True},
            headers=h,
        )
        assert res.status_code == 200

        # Batch write not found and batch update corrupt
        corrupted_batch_name = f"corrupt_batch_update_{uid}"
        async with AsyncSessionLocal() as session:
            session.add(
                CPFile(
                    name=corrupted_batch_name,
                    content="{corrupted",
                    version=1,
                    updated_at=datetime.datetime.now(datetime.timezone.utc),
                )
            )
            await session.commit()

        edge_case_batch = {
            "operations": [
                {
                    "action": "write",
                    "resource_type": "ClassPlan",
                    "name": f"new_batch_write_{uid}",
                    "payload": {},
                },
                {
                    "action": "update",
                    "resource_type": "ClassPlan",
                    "name": corrupted_batch_name,
                    "payload": {"fixed": True},
                },
            ]
        }
        res = await ac.post(
            f"{_CMD_PREFIX}/datas/batch", json=edge_case_batch, headers=h
        )
        assert res.status_code == 200

        # Batch exception rollback
        from unittest.mock import patch

        mock_name = f"mocked_merge_{uid}"
        await ac.get(
            f"{_CMD_PREFIX}/datas/TimeLayout/create?name={mock_name}", headers=h
        )

        with patch(
            "app.api.command.dict_deep_merge",
            side_effect=Exception("Mocked Merge Error"),
        ):
            error_batch = {
                "operations": [
                    {
                        "action": "update",
                        "resource_type": "TimeLayout",
                        "name": mock_name,
                        "payload": {"a": 1},
                    }
                ]
            }
            res = await ac.post(
                f"{_CMD_PREFIX}/datas/batch", json=error_batch, headers=h
            )
            assert res.status_code == 200
            assert "内部错误" in res.json()["message"]


@pytest.mark.asyncio
async def test_resource_token_ttl_expiry():
    """覆盖 resource_token：基于 Redis TTL 的过期。"""
    from app.services.resource_token import create_token, resolve_token
    import asyncio

    token = await create_token(TEST_TENANT_ID, "ClassPlan", "test_res", ttl=1)
    assert token

    # Token should resolve now
    result = await resolve_token(token)
    assert result is not None

    # Wait for expiry (1 second TTL)
    await asyncio.sleep(1.2)

    result = await resolve_token(token)
    assert result is None


@pytest.mark.asyncio
async def test_client_details_endpoint(command_headers):
    from app.models.database import AsyncSessionLocal, ClientRecord
    import datetime
    import uuid

    transport = ASGITransport(app=management_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        h = command_headers
        # Client not found
        res = await ac.get(f"{_CMD_PREFIX}/client/{uuid.uuid4()}/details", headers=h)
        assert res.status_code == 404

        # Create a client and fetch details
        test_uid = f"detail-{uuid.uuid4()}"
        async with AsyncSessionLocal() as session:
            from app.core.tenant.context import set_search_path

            await set_search_path(session)
            session.add(
                ClientRecord(
                    uid=test_uid,
                    client_id="test-class",
                    mac="AABBCCDDEEFF",
                    registered_at=datetime.datetime.now(datetime.timezone.utc),
                )
            )
            await session.commit()

        res = await ac.get(f"{_CMD_PREFIX}/client/{test_uid}/details", headers=h)
        assert res.status_code == 200
        data = res.json()
        assert data["uid"] == test_uid
        assert data["status"] == "offline"


@pytest.mark.asyncio
async def test_client_status_with_session_manager(command_headers):
    transport = ASGITransport(app=management_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(f"{_CMD_PREFIX}/clients/status", headers=command_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_update_data_command(command_headers):
    transport = ASGITransport(app=management_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            f"{_CMD_PREFIX}/client/test-uid/update_data", headers=command_headers
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_send_notification_command(command_headers):
    transport = ASGITransport(app=management_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "MessageMask": "Test",
            "MessageContent": "Hello",
            "IsEmergency": True,
            "DurationSeconds": 10.0,
        }
        res = await ac.post(
            f"{_CMD_PREFIX}/client/test-uid/send_notification",
            json=payload,
            headers=command_headers,
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_get_config_command(command_headers):
    transport = ASGITransport(app=management_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            f"{_CMD_PREFIX}/client/test-uid/get_config?config_type=1",
            headers=command_headers,
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_command_endpoints_without_servicer(command_headers):
    transport = ASGITransport(app=management_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        h = command_headers
        orig_cmd = getattr(management_app.state, "command_servicer", None)
        orig_sm = getattr(management_app.state, "session_manager", None)

        try:
            management_app.state.command_servicer = None
            management_app.state.session_manager = None

            res = await ac.get(f"{_CMD_PREFIX}/clients/status", headers=h)
            assert res.status_code == 200
            assert res.json() == []

            res = await ac.get(f"{_CMD_PREFIX}/client/test-uid/restart", headers=h)
            assert res.json()["status"] == "error"

            res = await ac.get(f"{_CMD_PREFIX}/client/test-uid/update_data", headers=h)
            assert res.json()["status"] == "error"

            res = await ac.post(
                f"{_CMD_PREFIX}/client/test-uid/send_notification",
                json={"MessageContent": "x"},
                headers=h,
            )
            assert res.json()["status"] == "error"

            res = await ac.get(
                f"{_CMD_PREFIX}/client/test-uid/get_config?config_type=0", headers=h
            )
            assert res.json()["status"] == "error"
        finally:
            management_app.state.command_servicer = orig_cmd
            management_app.state.session_manager = orig_sm
