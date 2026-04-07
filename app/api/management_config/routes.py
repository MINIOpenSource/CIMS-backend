"""引导配置生成服务。

由租户子域名访问，动态下发引导客户端加入管理服务的 JSON 配置文件。
支持通过 class_identity 匹配预注册客户端。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.pre_registered_client import PreRegisteredClient
from app.models.session import get_db
from app.core.tenant.context import get_tenant_id
from app.core.config import BASE_DOMAIN

router = APIRouter()


@router.get("/v1/management-config")
async def get_config(
    class_identity: str = "",
    db: AsyncSession = Depends(get_db),
):
    """根据子域名返回 ManagementPreset.json。

    若传入 class_identity 且匹配到预注册客户端，
    额外返回 PreRegisteredLabel 字段。
    """
    tenant_id = get_tenant_id()
    stmt = select(Account).where(Account.id == tenant_id)
    account = (await db.execute(stmt)).scalar_one_or_none()
    slug = account.slug if account else "unknown"

    # 尝试匹配预注册客户端
    label = ""
    if class_identity and account:
        pre_reg = (
            await db.execute(
                select(PreRegisteredClient).where(
                    PreRegisteredClient.account_id == account.id,
                    PreRegisteredClient.class_identity == class_identity,
                )
            )
        ).scalar_one_or_none()
        if pre_reg:
            label = pre_reg.label

    return {
        "IsManagementEnabled": True,
        "ManagementServerKind": 2,
        "ManagementServer": f"https://{slug}.{BASE_DOMAIN}",
        "ManagementServerGrpc": f"https://{slug}.{BASE_DOMAIN}",
        "ClassIdentity": class_identity,
        "PreRegisteredLabel": label,
        "ManifestUrlTemplate": "",
    }
