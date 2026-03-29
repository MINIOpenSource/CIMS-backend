"""用户信息响应、登录请求与管理员更新模型。"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserLoginRequest(BaseModel):
    """用户登录请求体。"""

    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., max_length=128)


class UserOut(BaseModel):
    """用户信息响应模型。"""

    id: str
    username: str
    email: str
    display_name: str
    role_code: str
    is_active: bool
    can_create_account: bool = False
    created_at: str


class UserUpdateRequest(BaseModel):
    """用户信息更新请求体（管理员用）。"""

    display_name: Optional[str] = Field(None, max_length=128)
    role_code: Optional[str] = Field(None, max_length=32)
    is_active: Optional[bool] = None
    can_create_account: Optional[bool] = None
