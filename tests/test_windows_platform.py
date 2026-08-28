from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from lanctl.infrastructure.platform.base import ServiceResult
from lanctl.infrastructure.platform.windows import WindowsPlatform
from lanctl.infrastructure.platform.windows_service import (
    SERVICE_CONTROL_STOP,
    SERVICE_RUNNING,
    SERVICE_STOPPED,
    WindowsServiceHost,
)


def completed(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


def test_service_dispatch_and_confirmation_gate(monkeypatch):
    platform = WindowsPlatform()
    monkeypatch.setattr(platform, "_status", lambda: ServiceResult(True, "running", "ok"))
    assert platform.service("STATUS").status == "running"
    assert platform.service("install").status == "blocked"
    assert platform.service("uninstall").status == "blocked"
    assert platform.service("unsupported").status == "unsupported"


def test_install_rejects_relative_paths(tmp_path):
    platform = WindowsPlatform()
    assert platform.service("install", confirm=True, executable="relative.exe").status == "error"
    assert (
        platform.service(
            "install",
            confirm=True,
            command=[str(tmp_path / "service.exe")],
            data_dir="relative",
        ).status
        == "error"
    )


def test_install_reports_acl_and_registration_failures(tmp_path, monkeypatch):
    platform = WindowsPlatform()
    executable, data = tmp_path / "service.exe", tmp_path / "data"
    monkeypatch.setattr(platform, "_run", lambda _args: completed(1, stderr="denied"))
    assert (
        platform.service(
            "install", confirm=True, command=[str(executable)], data_dir=str(data)
        ).status
        == "error"
    )

    calls = iter([completed(), completed(1, stderr="sc failed")])
    monkeypatch.setattr(platform, "_run", lambda _args: next(calls))
    monkeypatch.setattr(
        platform,
        "_status",
        lambda: ServiceResult(True, "not-installed", "", {"installed": False}),
    )
    assert (
        platform.service(
            "install", confirm=True, command=[str(executable)], data_dir=str(data)
        ).status
        == "error"
    )


def test_uninstall_and_controls_cover_idempotent_states(monkeypatch):
    platform = WindowsPlatform()
    states = {
        "missing": ServiceResult(True, "not-installed", "", {"installed": False}),
        "running": ServiceResult(True, "running", "", {"installed": True, "running": True}),
        "stopped": ServiceResult(True, "stopped", "", {"installed": True, "running": False}),
    }
    monkeypatch.setattr(platform, "_status", lambda: states["missing"])
    assert platform._uninstall().status == "not-installed"
    assert platform._control("start").status == "not-installed"

    monkeypatch.setattr(platform, "_status", lambda: states["running"])
    assert platform._control("start").status == "running"
    monkeypatch.setattr(platform, "_status", lambda: states["stopped"])
    assert platform._control("stop").status == "stopped"

    monkeypatch.setattr(platform, "_run", lambda _args: completed(1, stderr="failure"))
    assert platform._control("start").status == "error"


@pytest.mark.parametrize(
    ("result", "status", "installed", "running"),
    [
        (completed(1, stderr="OpenService FAILED 1060"), "not-installed", False, False),
        (completed(1, stderr="access denied"), "error", False, False),
        (completed(0, stdout="STATE: RUNNING"), "running", True, True),
        (completed(0, stdout="STATE: STOPPED"), "stopped", True, False),
    ],
)
def test_status_parsing(monkeypatch, result, status, installed, running):
    monkeypatch.setattr(WindowsPlatform, "_run", staticmethod(lambda _args: result))
    value = WindowsPlatform()._status()
    assert (value.status, value.detail["installed"], value.detail["running"]) == (
        status,
        installed,
        running,
    )


def test_wait_success_and_timeout(monkeypatch):
    platform = WindowsPlatform()
    running = ServiceResult(True, "running", "", {"installed": True, "running": True})
    monkeypatch.setattr(platform, "_status", lambda: running)
    assert platform._wait(True, timeout=0).status == "running"
    assert platform._wait(False, timeout=0).status == "error"


def test_run_converts_process_errors(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("x"))
    )
    result = WindowsPlatform._run(["sc.exe"])
    assert result.returncode == 1 and "x" in result.stderr


class NativeCall:
    def __init__(self, result=1):
        self.result = result
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self.result


def native_api(register=1):
    return SimpleNamespace(
        StartServiceCtrlDispatcherW=NativeCall(),
        RegisterServiceCtrlHandlerExW=NativeCall(register),
        SetServiceStatus=NativeCall(),
    )


def test_service_host_control_and_successful_runner():
    host = WindowsServiceHost("TestService")
    host._advapi32 = native_api()
    host._runner = lambda stop_event: stop_event.set()
    host._service_main(0, None)
    assert host.status.dwCurrentState == SERVICE_STOPPED
    assert host.stop_event.is_set()
    host.stop_event.clear()
    assert host._control_handler(SERVICE_CONTROL_STOP, 0, None, None) == 0
    assert host.stop_event.is_set()


def test_service_host_runner_failure_sets_nonzero_exit():
    host = WindowsServiceHost()
    host._advapi32 = native_api()
    host._runner = lambda _event: (_ for _ in ()).throw(RuntimeError("boom"))
    host._service_main(0, None)
    assert host.status.dwCurrentState == SERVICE_STOPPED
    assert host.status.dwWin32ExitCode == 1


def test_service_host_ignores_main_when_registration_fails():
    host = WindowsServiceHost()
    host._advapi32 = native_api(register=0)
    host._runner = lambda _event: pytest.fail("runner must not execute")
    host._service_main(0, None)
    assert host.status.dwCurrentState != SERVICE_RUNNING
