"""账户列表与搜索路由。

提供当前用户有权访问的账户列表、搜索及创建申请。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.account_out import AccountOut
from app.core.auth.dependencies import get_current_user_id
from app.models.account import Account
from app.models.account_member import AccountMember
from app.models.session import get_db

router = APIRouter()


def _out(a: Account) -> AccountOut:
    """将 ORM Account 实例转换为 AccountOut 响应模型。"""
    return AccountOut(
        id=a.id,
        name=a.name,
        slug=a.slug,
        api_key=a.api_key,
        is_active=a.is_active,
        created_at=a.created_at.isoformat(),
    )


@router.get("/list", response_model=list[AccountOut])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """列出当前用户有权限访问的所有账户。"""
    stmt = (
        select(Account)
        .join(AccountMember, Account.id == AccountMember.account_id)
        .where(AccountMember.user_id == user_id)
        .where(Account.is_active == True)  # noqa: E712
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_out(a) for a in rows]
