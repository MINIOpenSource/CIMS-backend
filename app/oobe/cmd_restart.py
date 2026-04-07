"""restart 子命令处理器。

通过 systemctl 重启 cims-backend 服务。
"""

import subprocess
import sys


def handle_restart() -> None:
    """处理 `cims restart` 子命令。

    调用 systemctl restart cims-backend 重启服务。
    若非 root 则自动使用 sudo。
    """
    import os

    cmd = ["systemctl", "restart", "cims-backend"]
    if os.geteuid() != 0:
        cmd = ["sudo"] + cmd

    print(f"⏳ 正在执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ cims-backend 已重启")
    else:
        print(f"❌ 重启失败: {result.stderr.strip()}")
        sys.exit(1)
