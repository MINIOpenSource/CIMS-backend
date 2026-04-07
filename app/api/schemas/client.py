"""客户端资源清单定义。

指定了从服务器同步至 ClassIsland 终端的资源结构。
"""

from typing import Any, Dict
from pydantic import BaseModel


class ClientManifest(BaseModel):
    """包含时间线、策略等所有必要配置的顶层对象。"""

    ClassPlanSource: Dict[str, Any]
    TimeLayoutSource: Dict[str, Any]
    SubjectsSource: Dict[str, Any]
    DefaultSettingsSource: Dict[str, Any]
    PolicySource: Dict[str, Any]
    ComponentsSource: Dict[str, Any]
    CredentialSource: Dict[str, Any]
    ServerKind: int = 1
    OrganizationName: str = "CIMS Server"
    CoreVersion: str = "2.0.0.0"
