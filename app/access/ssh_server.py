from __future__ import annotations
import socket,threading
try:
    import paramiko
    _Base=paramiko.ServerInterface
except ImportError:
    paramiko=None
    class _Base:pass
from .network import source_allowed

class RestrictedSshServer(_Base):
    """Servidor Paramiko que solo admite el subsystem restringido `lanctl`."""
    def __init__(self,auth,authorization,password_enabled=False,source_ip=""):
        super().__init__();self.auth=auth;self.authorization=authorization;self.password_enabled=password_enabled;self.source_ip=source_ip;self.user=None;self.subsystem=False
    def check_auth_publickey(self,username,key):
        if not self.auth or not paramiko:return 2
        try:self.user=self.auth.authenticate_ssh_key(username,f"{key.get_name()} {key.get_base64()}",self.source_ip);return paramiko.AUTH_SUCCESSFUL
        except (ValueError,PermissionError):return paramiko.AUTH_FAILED
    def check_auth_password(self,username,password):
        if not self.password_enabled or not self.auth or not paramiko:return 2
        try:self.user=self.auth.authenticate_password(username,password,self.source_ip);return paramiko.AUTH_SUCCESSFUL
        except (ValueError,PermissionError):return paramiko.AUTH_FAILED
    def get_allowed_auths(self,username):return "publickey,password" if self.password_enabled else "publickey"
    def check_channel_request(self,kind,chanid):return paramiko.OPEN_SUCCEEDED if paramiko and kind=="session" else (paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED if paramiko else False)
    def check_channel_shell_request(self,channel):return False
    def check_channel_exec_request(self,channel,command):return False
    def check_channel_subsystem_request(self,channel,name):self.subsystem=name=="lanctl";return self.subsystem
    def check_channel_x11_request(self,*args):return False
    def check_channel_forward_agent_request(self,*args):return False
    def check_port_forward_request(self,*args):return False
    def cancel_port_forward_request(self,*args):return False
    @staticmethod
    def capability():return {"available":bool(paramiko),"backend":"paramiko" if paramiko else None,"reason":None if paramiko else "instala paramiko"}

class SshAccessServer:
    def __init__(self,bind,port,cidr,host_key,auth,password_enabled=False):self.bind,self.port,self.cidr,self.host_key,self.auth,self.password_enabled=bind,port,cidr,host_key,auth,password_enabled;self.closed=threading.Event();self.socket=None
    def serve_forever(self):
        if not paramiko:raise RuntimeError("capability SSH no disponible: falta paramiko")
        listener=socket.socket();listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind((self.bind,self.port));listener.listen(16);listener.settimeout(1);self.socket=listener;key=paramiko.Ed25519Key.from_private_key_file(self.host_key)
        try:
            while not self.closed.is_set():
                try:client,address=listener.accept()
                except socket.timeout:continue
                if not source_allowed(address[0],self.cidr):client.close();continue
                threading.Thread(target=self._client,args=(client,address[0],key),daemon=True).start()
        finally:listener.close()
    def _client(self,client,source,key):
        transport=paramiko.Transport(client);transport.add_server_key(key);server=RestrictedSshServer(self.auth,None,self.password_enabled,source)
        try:
            transport.start_server(server=server);channel=transport.accept(15)
            if channel and server.subsystem and server.user:
                channel.send(b"LANCTL restricted console\r\nCommands are provided by the LANCTL command adapter.\r\n");channel.close()
        finally:transport.close()
    def stop(self):self.closed.set()
