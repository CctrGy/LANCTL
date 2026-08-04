from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class NetworkIdentity:
    cidr:str="";gatewayIp:str="";gatewayMac:str="";interface:str="";localIp:str="";confidence:str="unknown";evidence:tuple[str,...]=()

class IdentityResolver:
    def __init__(self,provider):self.provider=provider
    def resolve(self):return self.provider.identity()
    def validate(self,expected:NetworkIdentity,actual:NetworkIdentity,confirm=False):
        conflicts=[]
        for field in ("gatewayMac","gatewayIp","cidr"):
            left=getattr(expected,field);right=getattr(actual,field)
            if left and right and left.casefold()!=right.casefold():conflicts.append(field)
        if conflicts and not confirm:raise PermissionError("la identidad de la LAN no coincide: "+", ".join(conflicts))
        return not conflicts
