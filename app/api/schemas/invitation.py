"""邀请相关数据传输模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InvitationCreate(BaseModel):
    """创建邀请请求。"""

    role_in_account: str = Field("member", max_length=32)
    max_uses: int = Field(1, ge=1, le=100)
    expires_at: Optional[datetime] = None


class InvitationOut(BaseModel):
    """邀请响应。"""

    id: str
    account_id: str
    inviter_user_id: str
    code: str
    role_in_account: str
    max_uses: int
    used_count: int
    expires_at: Optional[str] = None
    is_active: bool
    created_at: str
