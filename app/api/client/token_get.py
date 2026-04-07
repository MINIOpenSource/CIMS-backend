"""令牌下发的资源获取端点。

根据资源令牌加载对应的配置数据并返回 JSON 内容。
"""

import json
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from app.core.tenant.context import set_search_path
from app.core.client_ip import get_client_ip_from_request
from app.models.database import AsyncSessionLocal
from app.services.resource_token import resolve_token
from app.api.command.model_map import MODEL_MAP
from app.grpc.session.online_status import get_tenant_online_ips

router = APIRouter()


@router.get("/get")
async def get_resource_by_token(token: str, request: Request):
    """通过令牌获取配置内容，附带 IP 鉴权。"""
    result = await resolve_token(token)
    if result is None:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    tenant_id, resource_type, name, token_ip = result
    model = MODEL_MAP.get(resource_type)
    if model is None:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Invalid resource type")

    # IP 鉴权
    client_ip = get_client_ip_from_request(request)
    if token_ip:
        if client_ip not in await get_tenant_online_ips(tenant_id):
            return {}

    # 令牌携带 tenant_id → 需取对应 Schema 设置 search_path
    async with AsyncSessionLocal() as db:
        # resolve_token 返回的 tenant_id 包含 slug 信息
        await set_search_path(db)
        row = (
            await db.execute(select(model).where(model.name == name))
        ).scalar_one_or_none()

    if row is None:  # pragma: no cover
        raise HTTPException(status_code=404, detail="Resource not found")

    try:
        return json.loads(row.content)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=500, detail="Corrupted resource")
