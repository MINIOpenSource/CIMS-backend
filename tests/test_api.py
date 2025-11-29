from fastapi.testclient import TestClient
from cims.ManagementServer.api import api, get_tenant_id
from cims.database.models import Tenant, Resource, ProfileConfig
from cims.database.connection import SessionLocal
import pytest


# Override dependency to return a test tenant ID
def override_get_tenant_id():
    return 1


api.dependency_overrides[get_tenant_id] = override_get_tenant_id

client = TestClient(api)


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    # Ensure test tenant exists
    if not session.query(Tenant).filter_by(id=1).first():
        session.add(Tenant(id=1, name="test_tenant"))
        session.commit()
    yield session
    session.close()


def test_read_main():
    response = client.get("/api/refresh")
    assert response.status_code == 200


def test_get_manifest(db_session):
    # Setup data
    uid = "test_client_uid"
    config = {
        "ClassPlan": "cp1",
        "TimeLayout": "tl1",
        "Subjects": "s1",
        "Settings": "set1",
        "Policy": "p1",
    }

    # Clean old data
    db_session.query(ProfileConfig).filter_by(uid=uid).delete()
    db_session.commit()

    db_session.add(ProfileConfig(tenant_id=1, uid=uid, config=config))
    db_session.commit()

    response = client.get(f"/api/v1/client/{uid}/manifest")
    assert response.status_code == 200
    data = response.json()
    assert "ClassPlanSource" in data
    assert "Version" in data["ClassPlanSource"]
    assert "cp1" in data["ClassPlanSource"]["Value"]


def test_get_policy(db_session):
    # Setup data
    res_type = "Policy"
    name = "default"
    data_content = {"policy_key": "policy_value"}

    # Clean old data
    db_session.query(Resource).filter_by(resource_type=res_type, name=name).delete()
    db_session.commit()

    db_session.add(
        Resource(tenant_id=1, resource_type=res_type, name=name, data=data_content)
    )
    db_session.commit()

    response = client.get(f"/api/v1/client/{res_type}?name={name}")
    assert response.status_code == 200
    assert response.json() == data_content


def test_get_policy_not_found():
    response = client.get("/api/v1/client/Policy?name=non_existent")
    assert response.status_code == 404
