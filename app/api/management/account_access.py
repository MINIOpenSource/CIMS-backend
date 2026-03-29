"""访问控制 — 列出与辅助。

提供成员列表查询和模型转换辅助。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.access import AccessMemberOut
from app.core.auth.dependencies import get_current_user_id
from app.models.account_member import AccountMember
from app.models.session import get_db

router = APIRouter()


def _member_out(m: AccountMember) -> AccessMemberOut:
    """模型转响应。"""
    return AccessMemberOut(
        id=m.id,
        user_id=m.user_id,
        account_id=m.account_id,
        role_in_account=m.role_in_account,
        joined_at=str(m.joined_at),
    )


@router.get("/list", response_model=list[AccessMemberOut])
async def list_access(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """列出账户下的具权用户。"""
    rows = (
        (
            await db.execute(
                select(AccountMember).where(AccountMember.account_id == account_id)
            )
        )
        .scalars()
        .all()
    )
    return [_member_out(m) for m in rows]


@router.post("/{user_id}/rename")
async def rename_access(account_id: str, user_id: str):
    """重命名具权用户。"""
    return {"message": "暂未实现"}


@router.get("/{user_id}")
async def get_access_detail(
    account_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _uid: str = Depends(get_current_user_id),
):
    """获取具权用户信息。"""
    from sqlalchemy import and_

    m = (
        await db.execute(
            select(AccountMember).where(
                and_(
                    AccountMember.account_id == account_id,
                    AccountMember.user_id == user_id,
                )
            )
        )
    ).scalar_one_or_none()
    if not m:
        from fastapi import HTTPException

        raise HTTPException(404, "成员不存在")
    return _member_out(m)
