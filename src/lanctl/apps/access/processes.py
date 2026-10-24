"""Process adapter shared by local access commands and settings."""

import os
import platform
import subprocess
from uuid import uuid4

from lanctl.bootstrap.commands import ip_command
from lanctl.core.paths import service_data_scope


def start_service_process(service, protocol):
    from .runtime_state import _alive, _read, _ready, _stop_owner, _wait

    scope = "service" if service_data_scope() else "user"
    command = ip_command(
        "access",
        "serve",
        protocol,
        "--config",
        str(service.config_path),
        "--users",
        str(service.store.path),
        "--scope",
        scope,
    )
    environment = dict(os.environ)
    environment["LANCTL_DATA_SCOPE"] = scope
    environment.pop("LANCTL_SERVICE_MODE", None)
    token = uuid4().hex
    environment["LANCTL_ACCESS_START_TOKEN"] = token
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if platform.system() == "Windows" else 0
    process = subprocess.Popen(
        command,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=environment,
    )
    try:
        # Windows virtualenv launchers can wrap a different Python PID. The
        # actual child claims its identity before opening a listener.
        def claimed():
            if process.poll() is not None:
                raise RuntimeError("El proceso remoto terminó antes de registrar su identidad")
            owner = _read(service, protocol)
            return (
                owner.get("state") == "starting" and owner.get("token") == token and _alive(owner)
            )

        _wait(claimed, "El proceso remoto no registró su identidad")
        owner = _read(service, protocol)
        service.update_config(
            lambda config: config[protocol].update(
                processId=owner["processId"],
                processIdentity=owner["processIdentity"],
                processToken=token,
            )
        )
        settings = service.config()[protocol]

        def ready():
            if process.poll() is not None:
                raise RuntimeError("El proceso remoto terminó antes de confirmar el listener")
            return _ready(service, protocol, settings, "user")

        _wait(ready, "El proceso remoto no confirmó su arranque")
    except BaseException:
        # Popen retains the process handle; never signal a possibly recycled PID.
        owner = _read(service, protocol)
        if owner.get("token") == token:
            _stop_owner(owner)
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=8)

        def clear(config):
            if config[protocol].get("processToken") == token:
                for key in ("processId", "processIdentity", "processToken"):
                    config[protocol].pop(key, None)

        service.update_config(clear)
        raise
    return process


def _await_start_claim(service, protocol):
    """An unclaimed child never opens a socket, including after parent death."""
    from .runtime_state import _publish, _wait

    token = os.environ.get("LANCTL_ACCESS_START_TOKEN")
    if token:
        _publish(service, protocol, service.config()[protocol], "starting", "user", token=token)
        _wait(
            lambda: (
                service.config()[protocol].get("processToken") == token
                and service.config()[protocol].get("processId") == os.getpid()
            ),
            "El administrador no registró el proceso remoto",
        )


def _run_service_child(arguments):
    import argparse

    from lanctl.apps.ip.interfaces.cli.commands.access import register_access_command

    parser = argparse.ArgumentParser(prog="LANIP")
    register_access_command(parser.add_subparsers())
    args = parser.parse_args(arguments)
    try:
        return args.handler(args)
    except (OSError, RuntimeError, ValueError) as error:
        from lanctl.core.errors import errors

        errors.from_exception(
            error,
            origin="LANCTL.Access.Process.Start",
            code="ACCESS.PROCESS.START.FAILED",
            level=47,
            print_output=False,
        )
        return 2
