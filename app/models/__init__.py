"""CIMS 数据库模型聚合。

集中暴露所有实体模型，以便在整个项目内实现整洁的导入。
"""

from .base import Base
from .user import User
from .custom_role import CustomRole
from .account import Account
from .account_member import AccountMember
from .permission_def import PermissionDef
from .member_permission import MemberPermission
from .account_quota import AccountQuota
from .system_config import SystemConfig
from .reserved_name import ReservedName
from .resource_files import (
    CPFile,
    TLFile,
    SubFile,
    PolicyFile,
    SettingsFile,
    ComponentsFile,
    CredentialsFile,
)
from .client import ClientRecord, ClientProfile
from .audit import AuditLog
from .config_upload import ConfigUploadRecord
from .pairing import PairingCode
from .role_permission import RolePermission
from .pre_registered_client import PreRegisteredClient
from .invitation import Invitation
from .engine import AsyncSessionLocal, init_db
from .session import get_db

__all__ = [
    "Base",
    "User",
    "CustomRole",
    "Account",
    "AccountMember",
    "PermissionDef",
    "MemberPermission",
    "AccountQuota",
    "SystemConfig",
    "ReservedName",
    "CPFile",
    "TLFile",
    "SubFile",
    "PolicyFile",
    "SettingsFile",
    "ComponentsFile",
    "CredentialsFile",
    "ClientRecord",
    "ClientProfile",
    "AuditLog",
    "ConfigUploadRecord",
    "PairingCode",
    "RolePermission",
    "PreRegisteredClient",
    "Invitation",
    "AsyncSessionLocal",
    "init_db",
    "get_db",
]
