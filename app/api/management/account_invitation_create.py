"""邀请创建路由。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.invitation import InvitationCreate, InvitationOut
from app.core.auth.dependencies import get_current_user_id
from app.models.invitation import Invitation
from app.models.session import get_db
from .account_invitation import _out

router = APIRouter()


@router.post("/create", response_model=InvitationOut, status_code=201)
async def create_invitation(
    account_id: str,
    body: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    uid: str = Depends(get_current_user_id),
):
    """创建新邀请码。"""
    inv = Invitation(
        account_id=account_id,
        inviter_user_id=uid,
        role_in_account=body.role_in_account,
        max_uses=body.max_uses,
        expires_at=body.expires_at,
        created_at=datetime.now(timezone.utc),
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return _out(inv)
