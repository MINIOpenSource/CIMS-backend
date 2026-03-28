"""系统设置请求模型。

仅允许白名单内的配置项写入。
"""

from pydantic import BaseModel, field_validator, Field

# 允许写入的配置键白名单
ALLOWED_KEYS = {
    "registration_open",
    "require_approval",
    "max_accounts_per_user",
    "default_role",
    "motd",
}


class SettingsUpdate(BaseModel):
    """系统设置修改请求体。"""

    items: dict[str, str] = Field(
        ..., description="键值对，键必须在白名单内"
    )

    @field_validator("items")
    @classmethod
    def _check_keys(cls, v: dict[str, str]) -> dict[str, str]:
        """校验所有 key 是否在白名单中。"""
        bad = set(v.keys()) - ALLOWED_KEYS
        if bad:
            raise ValueError(f"不允许的配置项: {', '.join(bad)}")
        return v
