"""预注册客户端详情路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import BASE_DOMAIN
from app.models.account import Account
from app.models.pre_registered_client import PreRegisteredClient
from app.models.session import get_db
from .account_pre_reg_crud import _to_out

router = APIRouter()


@router.get("/{pre_reg_id}")
async def get_pre_reg(
    account_id: str,
    pre_reg_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取预注册客户端信息。"""
    row = (
        await db.execute(
            select(PreRegisteredClient).where(
                PreRegisteredClient.id == pre_reg_id,
                PreRegisteredClient.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "预注册客户端不存在")
    return _to_out(row)


@router.delete("/{pre_reg_id}", status_code=204)
async def delete_pre_reg(
    account_id: str,
    pre_reg_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除预注册客户端。"""
    row = (
        await db.execute(
            select(PreRegisteredClient).where(
                PreRegisteredClient.id == pre_reg_id,
                PreRegisteredClient.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "预注册客户端不存在")
    await db.delete(row)
    await db.commit()


@router.post("/{pre_reg_id}/rename")
async def rename_pre_reg(account_id: str, pre_reg_id: str):
    """重命名预注册客户端。"""
    return {"message": "暂未实现"}


@router.post("/{pre_reg_id}/enable")
async def enable_pre_reg(account_id: str, pre_reg_id: str):
    """启用预注册客户端。"""
    return {"message": "暂未实现"}


@router.post("/{pre_reg_id}/disable")
async def disable_pre_reg(account_id: str, pre_reg_id: str):
    """禁用预注册客户端。"""
    return {"message": "暂未实现"}


@router.post("/{pre_reg_id}/config")
async def config_pre_reg(account_id: str, pre_reg_id: str):
    """修改预注册客户端使用的档案组。"""
    return {"message": "暂未实现"}
