"""预注册客户端引导配置路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import BASE_DOMAIN
from app.models.account import Account
from app.models.pre_registered_client import PreRegisteredClient
from app.models.session import get_db

router = APIRouter()


@router.get("/{pre_reg_id}/ManagementPreset.json")
async def download_preset(
    account_id: str,
    pre_reg_id: str,
    db: AsyncSession = Depends(get_db),
):
    """下载预注册客户端的引导配置。"""
    acct = (
        await db.execute(select(Account).where(Account.id == account_id))
    ).scalar_one_or_none()
    if not acct or not acct.is_active:
        raise HTTPException(404, "账户不存在或已停用")
    pre_reg = (
        await db.execute(
            select(PreRegisteredClient).where(
                PreRegisteredClient.id == pre_reg_id,
                PreRegisteredClient.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not pre_reg:
        raise HTTPException(404, "预注册客户端不存在")
    return {
        "IsManagementEnabled": True,
        "ManagementServerKind": 1,
        "ManagementServer": f"https://{acct.slug}.{BASE_DOMAIN}",
        "ManagementServerGrpc": f"https://{acct.slug}.{BASE_DOMAIN}",
        "ClassIdentity": pre_reg.class_identity,
        "ManifestUrlTemplate": "",
    }
