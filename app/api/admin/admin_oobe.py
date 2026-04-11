"""OOBE 生命周期专用接口。

提供配对码换取临时权限 Token，并最终接收初始化字典落盘数据库等。
一旦流程成功后将立即自启动退出接管态并加载常态应用。
"""

import os
import sys
from fastapi import APIRouter, Form, HTTPException

from app.core.security.oobe_guard import verify_oobe_passcode, verify_oobe_token
from app.core.security.oobe_guard import OOBE_TOKEN
from app.oobe.initializer import write_config_file, init_database

router = APIRouter(prefix="/oobe", tags=["OOBE"])


@router.post("/verify")
async def verify_passcode(passcode: str = Form(...)):
    """校验终端的配对输入，并分发提权执行许可 Token。"""
    if not verify_oobe_passcode(passcode):
        raise HTTPException(status_code=403, detail="配对码错误或已失效")
    return {"token": OOBE_TOKEN}


@router.post("/configure")
async def configure_system(
    token: str = Form(...),
    db_url: str = Form(...),
    redis_url: str = Form(...),
    domain: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    """验证 Token 后进行数据库写入，若成功则触发自重启。"""
    if not verify_oobe_token(token):
        raise HTTPException(status_code=403, detail="非法令牌或已过期")

    config = {
        "db_url": db_url,
        "redis_url": redis_url,
        "domain": domain,
        "username": username,
        "email": email,
        "password": password,
    }

    try:
        write_config_file(config)
        await init_database(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"初始化受挫: {str(e)}")

    import threading

    threading.Timer(
        1.0, lambda: os.execv(sys.executable, [sys.executable] + sys.argv)
    ).start()
    return {"msg": "初始化完毕，系统重启中"}
