from __future__ import annotations
import socket
from time import monotonic
from .models import CheckResult,CheckSpec
from app.services.element_scanner import ping_details
from app.services.lan_scanner import active_arp_mac

class CheckRegistry:
    def __init__(self):self._items={}
    def register(self,spec:CheckSpec):
        if not spec.check_id or spec.check_id in self._items: raise ValueError("check ya registrado o sin id")
        if not callable(spec.handler) or spec.minimum_interval<5 or not .05<=spec.timeout<=120: raise ValueError("contrato de check no válido")
        self._items[spec.check_id]=spec; return spec
    def get(self,check_id):
        try:return self._items[check_id]
        except KeyError as error:raise ValueError(f"check no registrado: {check_id}") from error
    def list(self):return list(self._items.values())
    def remove_owner(self,owner):self._items={k:v for k,v in self._items.items() if v.owner!=owner}

def availability(target,timeout=.8)->CheckResult:
    started=monotonic(); ip=target.ip
    arp=bool(active_arp_mac(ip,timeout)); ping,latency,_ttl=ping_details(ip,timeout)
    return CheckResult("availability",target.device_id,arp or ping,latencyMs=latency,evidence=tuple(x for x,v in (("ARP",arp),("ICMP",ping)) if v),metrics={"durationMs":int((monotonic()-started)*1000)})

def tcp_port(target,port,timeout=.8)->CheckResult:
    try:
        with socket.create_connection((target.ip,int(port)),timeout=timeout): success=True
    except OSError:success=False
    return CheckResult(f"tcp.{port}",target.device_id,success,evidence=("TCP",),metrics={"port":int(port)})
