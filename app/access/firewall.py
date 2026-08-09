from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass

from .network import validate_endpoint


@dataclass(frozen=True)
class FirewallRule:
    protocol: str
    name: str
    bind: str
    cidr: str
    port: int


class FirewallManager:
    def __init__(self, system=None, runner=subprocess.run):
        self.system = system or platform.system()
        self.runner = runner

    def add(self, protocol, bind, cidr, port):
        bind, cidr, port = validate_endpoint(bind, cidr, port)
        name = f"LANCTL {protocol.upper()} LAN only"
        rule = FirewallRule(protocol, name, bind, cidr, port)
        command = self._command(rule, False)
        completed = self.runner(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            raise RuntimeError("no se pudo crear la regla de firewall limitada a la LAN")
        return rule

    def remove(self, rule):
        completed = self.runner(
            self._command(rule, True), capture_output=True, text=True, check=False
        )
        if completed.returncode:
            raise RuntimeError("no se pudo revertir la regla de firewall")

    def _command(self, rule, remove):
        if self.system == "Windows":
            if remove:
                return [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "delete",
                    "rule",
                    f"name={rule.name}",
                    "dir=in",
                ]
            return [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule.name}",
                "dir=in",
                "action=allow",
                "protocol=TCP",
                f"localip={rule.bind}",
                f"localport={rule.port}",
                f"remoteip={rule.cidr}",
                "profile=private",
            ]
        if self.system == "Linux":
            prefix = ["ufw", "delete"] if remove else ["ufw"]
            return [
                *prefix,
                "allow",
                "from",
                rule.cidr,
                "to",
                rule.bind,
                "port",
                str(rule.port),
                "proto",
                "tcp",
            ]
        raise RuntimeError("gestión de firewall no soportada en esta plataforma")
