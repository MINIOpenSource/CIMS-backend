"""monit 子命令处理器。

滚动查看 cims-backend 服务日志。
"""

import subprocess
import sys
from pathlib import Path


def handle_monit() -> None:
    """处理 `cims monit` 子命令。

    优先使用 journalctl 跟踪 systemd 日志，
    若 journalctl 不可用则回退到 tail -f 日志文件。
    """
    # 优先尝试 journalctl
    if _try_journalctl():
        return

    # 回退到 tail -f 日志文件
    log_dir = Path(".cims") / "logs"
    if not log_dir.exists():
        print("❌ 日志目录不存在。请先启动服务: cims start")
        sys.exit(1)

    log_files = sorted(log_dir.glob("cims-*.log"))
    if not log_files:
        print("❌ 无日志文件。请先启动服务: cims start")
        sys.exit(1)

    latest = log_files[-1]
    print(f"📋 正在监控日志: {latest}")
    print("   按 Ctrl+C 退出\n")

    try:
        subprocess.run(
            ["tail", "-f", "-n", "100", str(latest)],
            check=False,
        )
    except KeyboardInterrupt:
        print("\n👋 已退出日志监控")


def _try_journalctl() -> bool:
    """尝试使用 journalctl 查看服务日志。

    Returns:
        成功启动则返回 True，不可用或失败返回 False。
    """
    # 检查 journalctl 是否存在
    from shutil import which

    if not which("journalctl"):
        return False

    # 检查服务是否在 systemd 中注册
    check = subprocess.run(
        ["systemctl", "cat", "cims-backend"],
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        return False

    print("📋 正在监控 systemd 日志 (cims-backend)")
    print("   按 Ctrl+C 退出\n")

    try:
        subprocess.run(
            [
                "journalctl",
                "-u",
                "cims-backend",
                "-f",
                "--no-pager",
                "-n",
                "100",
                "-o",
                "cat",
            ],
            check=False,
        )
    except KeyboardInterrupt:
        print("\n👋 已退出日志监控")

    return True
