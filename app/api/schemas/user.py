"""用户相关数据传输定义。

封装用户注册、登录请求和响应的 Pydantic 模型。
包含用户名、密码、邮箱的合规校验。
"""

import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# 用户名规则：3~64 位，仅字母数字下划线，且以字母开头
_USERNAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,63}$")
# 密码强度：至少包含大写、小写、数字各一个
_PWD_UPPER = re.compile(r"[A-Z]")
_PWD_LOWER = re.compile(r"[a-z]")
_PWD_DIGIT = re.compile(r"[0-9]")


class UserRegisterRequest(BaseModel):
    """用户注册请求体。用户名可选，留空自动生成。"""

    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=12, max_length=128)
    username: Optional[str] = Field(None, max_length=64)
    display_name: str = Field("", max_length=128)

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        """密码强度校验：至少含大小写字母和数字。"""
        if not _PWD_UPPER.search(v):
            raise ValueError("密码需包含至少一个大写字母")
        if not _PWD_LOWER.search(v):
            raise ValueError("密码需包含至少一个小写字母")
        if not _PWD_DIGIT.search(v):
            raise ValueError("密码需包含至少一个数字")
        return v

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: Optional[str]) -> Optional[str]:
        """用户名格式校验（若提供）。"""
        if v is not None and not _USERNAME_RE.match(v):
            raise ValueError("用户名需 3~64 位，字母开头，仅含字母数字下划线")
        return v
