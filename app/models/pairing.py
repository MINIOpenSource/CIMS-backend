"""配对码模型。

存储设备配对请求，支持管理员审批后放行注册。
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PairingCode(Base):
    """设备注册配对码记录。"""

    __tablename__ = "pairing_codes"

    # UUID4 主键
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # 8位配对码 [2346789ABCEFGHJKLMNPRSTWXYZ]
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    # 关联租户 ID
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    # 请求注册的客户端 UID
    client_uid: Mapped[str] = mapped_column(String, default="")
    # 客户端 ID（名称标识）
    client_id: Mapped[str] = mapped_column(String, default="")
    # 客户端 MAC 地址
    client_mac: Mapped[str] = mapped_column(String, default="")
    # 客户端 IP 地址
    client_ip: Mapped[str] = mapped_column(String, default="")
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # 是否已审批
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    # 是否已使用（注册完成）
    used: Mapped[bool] = mapped_column(Boolean, default=False)
