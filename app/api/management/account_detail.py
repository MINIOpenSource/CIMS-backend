"""账户详情与管理路由。

提供账户停用功能（需 owner 权限，级联清理关联数据）。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.models.account import Account
from app.models.account_member import AccountMember
from app.models.pre_registered_client import PreRegisteredClient
from app.models.session import get_db

router = APIRouter()


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    """停用账户（需 owner 权限，级联清理关联数据）。"""
    # 权限校验：仅 owner 可操作
    member = (await db.execute(
        select(AccountMember).where(
            AccountMember.account_id == account_id,
            AccountMember.user_id == uid,
        )
    )).scalar_one_or_none()
    if not member or member.role_in_account != "owner":
        raise HTTPException(403, "仅账户所有者可执行此操作")
    acct = (await db.execute(
        select(Account).where(Account.id == account_id)
    )).scalar_one_or_none()
    if not acct:
        raise HTTPException(404, "账户不存在")
    # 软删除 + 级联清理
    acct.is_active = False
    await db.execute(
        delete(AccountMember).where(
            AccountMember.account_id == account_id)
    )
    await db.execute(
        delete(PreRegisteredClient).where(
            PreRegisteredClient.account_id == account_id)
    )
    await db.commit()
    return {"message": "账户已停用，关联数据已清理"}
