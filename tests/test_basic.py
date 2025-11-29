import pytest
from cims.database.models import Tenant
from cims.database.connection import init_db, SessionLocal


@pytest.fixture(scope="module")
def db():
    # Setup: Use an in-memory SQLite database for testing
    # Note: connection.py uses a file-based DB by default, so we might need to override it
    # or just use the initialized DB file if acceptable for this scope.
    # For now, we'll use the default initialization which creates cims.db in appdirs.
    # To be safer/cleaner, we could override the engine, but let's test the actual init logic first.

    init_db()
    session = SessionLocal()
    yield session
    session.close()
    # Teardown: Remove data if needed (optional for SQLite file in tmp/user dir)


def test_db_initialization(db):
    """
    Verify that the database is initialized and tables are created.
    """
    # Check if tables exist by querying
    # This proves models are registered and create_all worked
    try:
        tenants = db.query(Tenant).all()
        assert isinstance(tenants, list)
    except Exception as e:
        pytest.fail(f"Database query failed: {e}")


def test_tenant_creation(db):
    """
    Verify we can create a tenant.
    """
    tenant_name = "test_tenant"
    # Cleanup previous run if file persisted
    existing = db.query(Tenant).filter_by(name=tenant_name).first()
    if existing:
        db.delete(existing)
        db.commit()

    new_tenant = Tenant(name=tenant_name)
    db.add(new_tenant)
    db.commit()

    saved_tenant = db.query(Tenant).filter_by(name=tenant_name).first()
    assert saved_tenant is not None
    assert saved_tenant.name == tenant_name
