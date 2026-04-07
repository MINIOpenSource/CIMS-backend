"""客户端资源访问重定向。

生成 IP 绑定的资源令牌并将客户端重定向到集中式 GET 端点。
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.core.tenant.context import get_tenant_id
from app.core.client_ip import get_client_ip_from_request
from app.services.resource_token.creator import create_token

router = APIRouter()

# 已注册的合法资源类型（在应用初始化时用于聚合校验）
VALID_RESOURCES = [
    "ClassPlan",
    "TimeLayout",
    "Subjects",
    "Policy",
    "DefaultSettings",
    "Components",
    "Credentials",
]


@router.get("/v1/client/{resource_type}")
async def get_client_resource(resource_type: str, name: str, request: Request):
    """根据协议规则重定向到令牌保护的下载端点。"""
    if resource_type not in VALID_RESOURCES:
        raise HTTPException(status_code=400, detail="Invalid resource")

    tenant_id = get_tenant_id()
    client_ip = get_client_ip_from_request(request)

    token = await create_token(tenant_id, resource_type, name, client_ip=client_ip)
    return RedirectResponse(url=f"/get?token={token}", status_code=302)
