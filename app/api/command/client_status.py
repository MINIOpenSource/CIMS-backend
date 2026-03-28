"""客户端在线状态监控。

提供终端的在线/离线状态查询和详细记录查看。
按 NewAPI.md: GET /list, GET /search, GET /{client_id}, GET /{client_id}/status,
DELETE /{client_id}, POST /{client_id}/rename, POST /{client_id}/disconnect,
POST /{client_id}/disable, POST /{client_id}/enable, POST /{client_id}/config
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, ClientRecord
from app.core.tenant.context import get_tenant_id

router = APIRouter()


@router.get("/list")
async def list_clients(db: AsyncSession = Depends(get_db)):
    """获取当前租户下所有已注册的客户端列表。"""
    return (await db.execute(select(ClientRecord.uid))).scalars().all()


@router.get("/search")
async def search_clients(
    q: str = "", db: AsyncSession = Depends(get_db)
):
    """搜索客户端。"""
    rows = (await db.execute(select(ClientRecord))).scalars().all()
    if not q:
        return [r.uid for r in rows]
    return [r.uid for r in rows if q.lower() in (r.uid or "").lower()]


@router.get("/{client_id}")
async def get_client_detail(
    client_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """查询特定客户端的注册详情及其当前在线状态。"""
    tid = get_tenant_id()
    record = (
        await db.execute(
            select(ClientRecord).where(ClientRecord.uid == client_id)
        )
    ).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="未找到设备")
    sm = getattr(request.app.state, "session_manager", None)
    online = await sm.is_client_online(tid, client_id) if sm else False
    return {
        "uid": record.uid,
        "name": record.client_id,
        "mac": record.mac,
        "status": "online" if online else "offline",
        "registered_at": (
            record.registered_at.isoformat() if record.registered_at else None
        ),
    }


@router.delete("/{client_id}")
async def delete_client(
    client_id: str, db: AsyncSession = Depends(get_db)
):
    """删除客户端。"""
    record = (
        await db.execute(
            select(ClientRecord).where(ClientRecord.uid == client_id)
        )
    ).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="未找到设备")
    await db.delete(record)
    await db.commit()
    return {"message": "已删除"}


@router.post("/{client_id}/rename")
async def rename_client(client_id: str, db: AsyncSession = Depends(get_db)):
    """重命名客户端。"""
    return {"message": "暂未实现", "client_id": client_id}


@router.get("/{client_id}/status")
async def get_client_status(
    client_id: str, request: Request
):
    """获取客户端在线状态。"""
    tid = get_tenant_id()
    sm = getattr(request.app.state, "session_manager", None)
    online = await sm.is_client_online(tid, client_id) if sm else False
    return {"client_id": client_id, "online": online}


@router.post("/{client_id}/disconnect")
async def disconnect_client(client_id: str, request: Request):
    """断开客户端连接。"""
    return {"message": "暂未实现", "client_id": client_id}


@router.post("/{client_id}/disable")
async def disable_client(client_id: str):
    """禁用客户端。"""
    return {"message": "暂未实现", "client_id": client_id}


@router.post("/{client_id}/enable")
async def enable_client(client_id: str):
    """启用客户端。"""
    return {"message": "暂未实现", "client_id": client_id}


@router.post("/{client_id}/config")
async def set_client_config(client_id: str):
    """修改客户端使用的档案组。"""
    return {"message": "暂未实现", "client_id": client_id}
