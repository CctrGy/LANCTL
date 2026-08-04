from .base import PlatformAdapter,ServiceResult
class WindowsPlatform(PlatformAdapter):
    def service(self,action,**kwargs):
        return ServiceResult(False,"unsupported","La instalación como servicio Windows aún no está disponible; usa foreground")
