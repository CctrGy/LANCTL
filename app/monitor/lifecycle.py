from __future__ import annotations
import json,os
from pathlib import Path

class SingletonLock:
    def __init__(self,path):self.path=Path(path);self.owned=False
    def acquire(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        try:fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:
            try:pid=int(json.loads(self.path.read_text())["pid"]);_process_alive(pid)
            except (OSError,ValueError,KeyError,json.JSONDecodeError):self.path.unlink(missing_ok=True);return self.acquire()
            raise RuntimeError(f"monitor ya activo con PID {pid}")
        with os.fdopen(fd,"w") as stream:json.dump({"pid":os.getpid()},stream)
        self.owned=True;return self
    def release(self):
        if self.owned:self.path.unlink(missing_ok=True);self.owned=False
    def status(self):
        if not self.path.exists():return {"running":False}
        try:pid=int(json.loads(self.path.read_text())["pid"]);_process_alive(pid);return {"running":True,"pid":pid}
        except (OSError,ValueError,KeyError,json.JSONDecodeError):return {"running":False,"stale":True}
    def __enter__(self):return self.acquire()
    def __exit__(self,*_):self.release()

def _process_alive(pid:int)->None:
    if os.name!="nt":os.kill(pid,0);return
    import ctypes
    handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,pid)
    if not handle:raise OSError("proceso no encontrado")
    ctypes.windll.kernel32.CloseHandle(handle)
