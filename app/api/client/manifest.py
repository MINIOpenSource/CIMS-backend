"""客户端清单（Manifest）生成。

为终端设备提供获取其动态配置集（课表等）的接口。
"""

import time
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.database import get_db, ClientProfile
from app.api.schemas.client import ClientManifest
from app.core.client_ip import get_client_ip_from_request

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/v1/client/{client_uid}/manifest", response_model=ClientManifest)
async def get_client_manifest(
    request: Request, client_uid: str, db: AsyncSession = Depends(get_db)
):
    """为请求的 UID 构建完整的 Manifest JSON 数据。"""
    slug = getattr(request.state, "tenant_slug", "Unknown")
    client_ip = get_client_ip_from_request(request)
    logger.info(
        "[%s] Client API 详细信息: 请求 Manifest (租户 Slug=%s, UUID=%s)", 
        client_ip, slug, client_uid
    )

    stmt = select(ClientProfile).where(ClientProfile.client_id == client_uid)
    result = await db.execute(stmt)
    p = result.scalar_one_or_none() or ClientProfile()

    # 若配置档案不完整则使用默认值
    cp = p.class_plan or "default_classplan"
    tl = p.time_layout or "default_timelayout"
    sub = getattr(p, "subjects", None) or "default"
    ds = getattr(p, "default_settings", None) or "default"
    pol = getattr(p, "policy", None) or "default"
    comp = getattr(p, "components", None) or "default"
    cred = getattr(p, "credentials", None) or "default"
    cur = int(time.time())

    return _build_manifest(request, cp, tl, sub, ds, pol, comp, cred, cur)


def _build_manifest(request: Request, cp, tl, sub, ds, pol, comp, cred, ver):
    """组装各资源源的 Manifest 结构体。"""

    def _src(rt, n):
        # 使用 request.url_for 生成完整的绝对 URL，并附带 name 参数
        # 目标端点为 resource.py 中的 get_client_resource
        url = request.url_for("get_client_resource", resource_type=rt)
        full_url = str(url.include_query_params(name=n))
        return {"Value": full_url, "Version": ver}

    return ClientManifest(
        ClassPlanSource=_src("ClassPlan", cp),
        TimeLayoutSource=_src("TimeLayout", tl),
        SubjectsSource=_src("Subjects", sub),
        DefaultSettingsSource=_src("DefaultSettings", ds),
        PolicySource=_src("Policy", pol),
        ComponentsSource=_src("Components", comp),
        CredentialSource=_src("Credentials", cred),
        ServerKind=1,
        OrganizationName="CIMS Server",
        CoreVersion="2.0.0.0",
    )
