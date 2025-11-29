from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    Float,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Tenant(Base):
    """
    Tenant model representing an organization or a group of users.
    """

    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    resources = relationship(
        "Resource", back_populates="tenant", cascade="all, delete-orphan"
    )
    clients = relationship(
        "Client", back_populates="tenant", cascade="all, delete-orphan"
    )
    client_statuses = relationship(
        "ClientStatus", back_populates="tenant", cascade="all, delete-orphan"
    )
    profile_configs = relationship(
        "ProfileConfig", back_populates="tenant", cascade="all, delete-orphan"
    )
    pre_registers = relationship(
        "PreRegister", back_populates="tenant", cascade="all, delete-orphan"
    )


class Resource(Base):
    """
    Resource model storing arbitrary data associated with a tenant.
    """

    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    data = Column(JSON, nullable=False)

    tenant = relationship("Tenant", back_populates="resources")


class Client(Base):
    """
    Client model representing a device or application instance.
    """

    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    uid = Column(String, nullable=False)
    client_id = Column(String, nullable=False)

    tenant = relationship("Tenant", back_populates="clients")
    __table_args__ = (UniqueConstraint("tenant_id", "uid", name="_tenant_uid_uc"),)


class ClientStatus(Base):
    """
    ClientStatus model tracking the online status and heartbeat of a client.
    """

    __tablename__ = "client_status"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    uid = Column(String, nullable=False)
    is_online = Column(Boolean, nullable=False)
    last_heartbeat = Column(Float, nullable=False)

    tenant = relationship("Tenant", back_populates="client_statuses")
    __table_args__ = (
        UniqueConstraint("tenant_id", "uid", name="_tenant_status_uid_uc"),
    )


class ProfileConfig(Base):
    """
    ProfileConfig model storing configuration profiles for clients.
    """

    __tablename__ = "profile_config"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    uid = Column(String, nullable=False)
    config = Column(JSON, nullable=False)

    tenant = relationship("Tenant", back_populates="profile_configs")
    __table_args__ = (
        UniqueConstraint("tenant_id", "uid", name="_tenant_profile_uid_uc"),
    )


class PreRegister(Base):
    """
    PreRegister model for storing pre-registration data for clients.
    """

    __tablename__ = "pre_register"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    client_id = Column(String, nullable=False)
    config = Column(JSON, nullable=False)

    tenant = relationship("Tenant", back_populates="pre_registers")
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "client_id", name="_tenant_preregister_client_id_uc"
        ),
    )
