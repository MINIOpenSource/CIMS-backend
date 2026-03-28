"""Management API 账户级聚合路由。

挂载所有 /account/* 下的子路由。
"""

from fastapi import APIRouter

from .account_list import router as list_r
from .account_search import router as search_r
from .account_apply import router as apply_r
from .account_detail import router as detail_r
from .account_info import router as info_r
from .account_resource import router as res_r
from .account_client import router as cli_r
from .account_pairing import router as pair_r
from .account_pairing_action import router as pair_act_r
from .account_pre_reg_crud import router as prereg_r
from .account_pre_reg_detail import router as prereg_d_r
from .account_pre_reg_preset import router as prereg_p_r
from .account_pre_reg_create import router as prereg_c_r
from .account_access import router as access_r
from .account_access_search import router as access_s_r
from .account_access_update import router as access_u_r
from .account_access_delete import router as access_d_r
from .account_invitation import router as inv_r
from .account_invitation_create import router as inv_c_r
from .account_invitation_revoke import router as inv_v_r
from .bulk import router as bulk_r

router = APIRouter()

# /account 顶层
router.include_router(list_r, prefix="/account", tags=["Account"])
router.include_router(search_r, prefix="/account", tags=["Account"])
router.include_router(apply_r, prefix="/account", tags=["Account"])

# /account/{account_id}/*
router.include_router(detail_r, prefix="/account", tags=["Account"])
router.include_router(info_r, prefix="/account", tags=["Account"])

# 资源（需账户上下文）
_acct = "/account/{account_id}"
router.include_router(res_r, prefix=f"{_acct}", tags=["Resource"])
router.include_router(cli_r, prefix=f"{_acct}/client", tags=["Client"])

# 配对码
router.include_router(pair_r, prefix=f"{_acct}/pairing", tags=["Pairing"])
router.include_router(pair_act_r, prefix=f"{_acct}/pairing", tags=["Pairing"])

# 预注册
_pre = f"{_acct}/pre-registration"
router.include_router(prereg_r, prefix=_pre, tags=["PreReg"])
router.include_router(prereg_d_r, prefix=_pre, tags=["PreReg"])
router.include_router(prereg_p_r, prefix=_pre, tags=["PreReg"])
router.include_router(prereg_c_r, prefix=_pre, tags=["PreReg"])

# 访问控制
_acc = f"{_acct}/access"
router.include_router(access_r, prefix=_acc, tags=["Access"])
router.include_router(access_s_r, prefix=_acc, tags=["Access"])
router.include_router(access_u_r, prefix=_acc, tags=["Access"])
router.include_router(access_d_r, prefix=_acc, tags=["Access"])

# 邀请
_inv = f"{_acct}/invitation"
router.include_router(inv_r, prefix=_inv, tags=["Invite"])
router.include_router(inv_c_r, prefix=_inv, tags=["Invite"])
router.include_router(inv_v_r, prefix=_inv, tags=["Invite"])

# 批量操作
router.include_router(bulk_r, prefix="/account/bulk", tags=["Bulk"])
