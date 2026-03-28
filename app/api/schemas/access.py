"""访问控制（成员权限）数据传输模型。"""

from pydantic import BaseModel, Field


class AccessMemberOut(BaseModel):
    """账户成员响应。"""

    id: str
    user_id: str
    account_id: str
    role_in_account: str
    joined_at: str


class AccessRoleUpdate(BaseModel):
    """修改成员角色请求。"""

    role_in_account: str = Field(
        ..., max_length=32, description="owner / admin / member / viewer"
    )
