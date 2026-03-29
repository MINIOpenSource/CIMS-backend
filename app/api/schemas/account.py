"""账户相关数据传输定义。

封装账户创建、修改和响应的 Pydantic 模型。
包含 Slug 的格式校验。
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Slug 规则：3~64 位，仅小写字母数字连字符，不以连字符开头/结尾
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,62}[a-z0-9]$")


class AccountCreate(BaseModel):
    """创建新账户的请求体。slug 可选，留空自动生成。"""

    name: str = Field(..., min_length=1, max_length=128)
    slug: Optional[str] = Field(None, min_length=3, max_length=64)

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, v: Optional[str]) -> Optional[str]:
        """Slug 格式校验（若提供）。"""
        if v is not None and not _SLUG_RE.match(v):
            raise ValueError(
                "Slug 需 3~64 位小写字母数字连字符，" "不以连字符开头/结尾"
            )
        return v


class AccountUpdate(BaseModel):
    """修改账户的请求体。"""

    name: Optional[str] = Field(None, max_length=128)
    slug: Optional[str] = Field(None, min_length=3, max_length=64)
    is_active: Optional[bool] = None

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, v: Optional[str]) -> Optional[str]:
        """Slug 格式校验（若提供）。"""
        if v is not None and not _SLUG_RE.match(v):
            raise ValueError("Slug 格式不合法")
        return v
