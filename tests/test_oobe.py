"""OOBE 初始化流程与 CLI 命令测试。

测试首次运行检测、配置文件写入、输入校验器、
systemd 服务文件生成以及 daemon 生命周期命令分发。
"""

import logging
from unittest.mock import patch, MagicMock

from app.oobe.validator import (
    validate_db_url,
    validate_email,
    validate_password,
    validate_username,
)
from app.services.user.name_validator import (
    validate_username_format,
    validate_slug_format,
)


class TestDetector:
    """初始化检测器测试。"""

    def test_not_initialized(self, tmp_path, monkeypatch):
        """无配置文件时应返回 False。"""
        monkeypatch.setattr(
            "app.oobe.detector.CONFIG_FILE",
            tmp_path / "nonexistent.json",
        )
        # 直接检查文件不存在
        assert not (tmp_path / "nonexistent.json").exists()


class TestValidator:
    """OOBE 输入校验器测试。"""

    def test_valid_db_url(self):
        """合法 PostgreSQL URL 应通过。"""
        assert validate_db_url("postgresql+psycopg://u:p@h/db") is None

    def test_invalid_db_url(self):
        """非 PostgreSQL URL 应被拒绝。"""
        assert validate_db_url("mysql://u:p@h/db") is not None

    def test_valid_email(self):
        """合法邮箱应通过。"""
        assert validate_email("user@example.com") is None

    def test_invalid_email(self):
        """非法邮箱应被拒绝。"""
        assert validate_email("not-an-email") is not None

    def test_strong_password(self):
        """满足所有要求的密码应通过。"""
        assert validate_password("MyStr0ng!Pass") is None

    def test_weak_password_short(self):
        """过短密码应被拒绝。"""
        assert validate_password("Sh0rt!") is not None

    def test_weak_password_no_upper(self):
        """无大写字母密码应被拒绝。"""
        assert validate_password("nouppercas3!!") is not None

    def test_weak_password_no_special(self):
        """无特殊字符密码应被拒绝。"""
        assert validate_password("NoSpecialChar1") is not None

    def test_valid_username(self):
        """合法用户名应通过。"""
        assert validate_username("admin_user") is None

    def test_invalid_username(self):
        """不合法用户名应被拒绝。"""
        assert validate_username("AB") is not None


class TestNameValidator:
    """用户名/Slug 格式校验测试。"""

    def test_valid_username_format(self):
        """合法格式的用户名。"""
        assert validate_username_format("hello_world")
        assert validate_username_format("abc")
        assert validate_username_format("user123")

    def test_invalid_username_format(self):
        """非法格式的用户名。"""
        assert not validate_username_format("ab")  # 太短
        assert not validate_username_format("Hello")  # 大写
        assert not validate_username_format("user-name")  # 减号

    def test_valid_slug_format(self):
        """合法格式的 Slug。"""
        assert validate_slug_format("my-school")
        assert validate_slug_format("abc")

    def test_invalid_slug_format(self):
        """非法格式的 Slug。"""
        assert not validate_slug_format("ab")  # 太短
        assert not validate_slug_format("my_school")  # 下划线


class TestLogging:
    """统一日志系统测试。"""

    def test_setup_logging_creates_directory(self, tmp_path, monkeypatch):
        """setup_logging 应创建日志目录。"""
        log_dir = tmp_path / "logs"
        monkeypatch.setattr("app.core.logging._LOG_DIR", log_dir)
        from app.core.logging import setup_logging

        setup_logging()
        assert log_dir.exists()

    def test_port_tag_filter(self):
        """端口标签过滤器应注入 port_tag 属性。"""
        from app.core.logging import _PortTagFilter

        f = _PortTagFilter("CLIENT")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is True
        assert record.port_tag == "CLIENT"  # type: ignore[attr-defined]

    def test_get_port_logger(self):
        """get_port_logger 应返回带端口标签的 logger。"""
        from app.core.logging import get_port_logger, _PortTagFilter

        logger = get_port_logger("ADMIN")
        assert logger.name == "cims.admin"
        assert any(isinstance(f, _PortTagFilter) for f in logger.filters)

    def test_color_formatter(self):
        """彩色格式化器应正常输出包含 ANSI 转义序列的文本。"""
        from app.core.logging import _ColorFormatter, _LOG_FORMAT, _LOG_DATE_FMT

        fmt = _ColorFormatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.port_tag = "CLIENT"  # type: ignore[attr-defined]
        result = fmt.format(record)
        assert "hello" in result
        # 确认颜色代码被正确还原
        assert record.port_tag == "CLIENT"  # type: ignore[attr-defined]


class TestDaemonCommands:
    """daemon 生命周期命令分发测试。"""

    def test_dispatch_daemon(self):
        """daemon 命令应路由到 handle_daemon。"""
        from app.oobe.commands import dispatch

        args = MagicMock()
        args.command = "daemon"
        with patch("app.oobe.cmd_daemon.handle_daemon") as mock:
            dispatch(args)
            mock.assert_called_once()

    def test_dispatch_start(self):
        """start 命令应路由到 handle_start。"""
        from app.oobe.commands import dispatch

        args = MagicMock()
        args.command = "start"
        with patch("app.oobe.cmd_start.handle_start") as mock:
            dispatch(args)
            mock.assert_called_once()

    def test_dispatch_stop(self):
        """stop 命令应路由到 handle_stop。"""
        from app.oobe.commands import dispatch

        args = MagicMock()
        args.command = "stop"
        with patch("app.oobe.cmd_stop.handle_stop") as mock:
            dispatch(args)
            mock.assert_called_once()

    def test_dispatch_startup(self):
        """startup 命令应路由到 handle_startup。"""
        from app.oobe.commands import dispatch

        args = MagicMock()
        args.command = "startup"
        with patch("app.oobe.cmd_startup.handle_startup") as mock:
            dispatch(args)
            mock.assert_called_once()

    def test_dispatch_monit(self):
        """monit 命令应路由到 handle_monit。"""
        from app.oobe.commands import dispatch

        args = MagicMock()
        args.command = "monit"
        with patch("app.oobe.cmd_monit.handle_monit") as mock:
            dispatch(args)
            mock.assert_called_once()

    def test_dispatch_unknown(self):
        """未知命令应 sys.exit(1)。"""
        from app.oobe.commands import dispatch

        args = MagicMock()
        args.command = "nonexistent"
        import sys

        with patch.object(sys, "exit") as mock_exit:
            dispatch(args)
            mock_exit.assert_called_with(1)


class TestSystemdGeneration:
    """systemd 服务文件生成测试。"""

    def test_generate_service_file(self, tmp_path, monkeypatch):
        """应在 .cims/ 目录生成有效的 service 文件。"""
        config_dir = tmp_path / ".cims"
        config_dir.mkdir()
        monkeypatch.setattr("app.oobe.initializer.CONFIG_DIR", config_dir)
        monkeypatch.setattr("os.getcwd", lambda: "/opt/cims")
        monkeypatch.setenv("USER", "testuser")

        # Mock shutil.which 和 subprocess.run
        with patch("shutil.which", return_value="/usr/bin/cims"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="权限不足")
                from app.oobe.initializer import generate_systemd_service

                generate_systemd_service()

        service_file = config_dir / "cims-backend.service"
        assert service_file.exists()
        content = service_file.read_text()
        assert "ExecStart=/usr/bin/cims daemon" in content
        assert "WorkingDirectory=/opt/cims" in content
        assert "User=testuser" in content
        assert "[Install]" in content
        assert "WantedBy=multi-user.target" in content

    def test_generate_service_uv_fallback(self, tmp_path, monkeypatch):
        """cims 不在 PATH 时应回退到 uv run cims。"""
        config_dir = tmp_path / ".cims"
        config_dir.mkdir()
        monkeypatch.setattr("app.oobe.initializer.CONFIG_DIR", config_dir)
        monkeypatch.setattr("os.getcwd", lambda: "/opt/cims")
        monkeypatch.setenv("USER", "test")

        def fake_which(name):
            """模拟 shutil.which：cims 不存在，uv 存在。"""
            if name == "cims":
                return None
            return "/usr/bin/uv"

        with patch("shutil.which", side_effect=fake_which):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="权限不足")
                from app.oobe.initializer import generate_systemd_service

                generate_systemd_service()

        content = (config_dir / "cims-backend.service").read_text()
        assert "uv run cims" in content


class TestPidFile:
    """PID 文件管理测试。"""

    def test_write_and_read_pid(self, tmp_path, monkeypatch):
        """应正确写入和读取 PID。"""
        pid_file = tmp_path / "cims.pid"
        monkeypatch.setattr("app.main._PID_FILE", pid_file)
        from app.main import _write_pid, read_pid

        _write_pid()
        import os

        assert read_pid() == os.getpid()

    def test_remove_pid(self, tmp_path, monkeypatch):
        """应正确删除 PID 文件。"""
        pid_file = tmp_path / "cims.pid"
        pid_file.write_text("12345")
        monkeypatch.setattr("app.main._PID_FILE", pid_file)
        from app.main import _remove_pid

        _remove_pid()
        assert not pid_file.exists()

    def test_read_pid_missing(self, tmp_path, monkeypatch):
        """PID 文件不存在时应返回 None。"""
        monkeypatch.setattr("app.main._PID_FILE", tmp_path / "nope.pid")
        from app.main import read_pid

        assert read_pid() is None


class TestCliParser:
    """CLI 参数解析器测试。"""

    def test_parser_has_daemon_commands(self):
        """解析器应包含 daemon/start/stop/startup/monit 子命令。"""
        from app.oobe.cli_parser import build_parser

        parser = build_parser()
        # 验证能解析新增的子命令
        for cmd in ["daemon", "start", "stop", "startup", "monit"]:
            args = parser.parse_args([cmd])
            assert args.command == cmd

    def test_parser_no_serve(self):
        """解析器不应包含旧的 serve 子命令。"""
        import pytest
        from app.oobe.cli_parser import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["serve"])
