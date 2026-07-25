from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import (
    HTTPDigestAuthHandler,
    HTTPPasswordMgrWithDefaultRealm,
    Request,
    build_opener,
)
import xml.etree.ElementTree as ET


SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"


@dataclass(frozen=True)
class Tr064Service:
    service_type: str
    service_id: str
    control_url: str
    scpd_url: str


class Tr064Client:
    """Cliente TR-064 con descubrimiento dinámico y autenticación Digest."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 49000,
        timeout: float = 5.0,
        opener=None,
    ):
        self.base_url = f"http://{host}:{port}/"
        self.timeout = timeout
        if opener is None:
            passwords = HTTPPasswordMgrWithDefaultRealm()
            passwords.add_password(None, self.base_url, username, password)
            opener = build_opener(HTTPDigestAuthHandler(passwords))
        self.opener = opener
        self._services: list[Tr064Service] | None = None

    def _open(self, request: Request | str) -> bytes:
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                return response.read()
        except HTTPError as error:
            if error.code in (401, 403):
                raise ValueError(
                    "TR-064 rechazó las credenciales del GATEWAY"
                ) from error
            detail = error.read().decode("utf-8", errors="replace")
            raise OSError(f"TR-064 respondió HTTP {error.code}: {detail[:160]}") from error
        except URLError as error:
            raise OSError(f"no se puede conectar con TR-064: {error.reason}") from error

    def discover(self) -> list[Tr064Service]:
        if self._services is not None:
            return self._services
        raw = self._open(urljoin(self.base_url, "tr64desc.xml"))
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as error:
            raise ValueError("TR-064 devolvió una descripción XML inválida") from error

        services: list[Tr064Service] = []
        for node in root.iter():
            if node.tag.rsplit("}", 1)[-1] != "service":
                continue
            fields = {
                child.tag.rsplit("}", 1)[-1]: (child.text or "").strip()
                for child in node
            }
            if fields.get("serviceType") and fields.get("controlURL"):
                services.append(
                    Tr064Service(
                        fields["serviceType"],
                        fields.get("serviceId", ""),
                        fields["controlURL"],
                        fields.get("SCPDURL", ""),
                    )
                )
        if not services:
            raise ValueError("el GATEWAY no ha publicado servicios TR-064")
        self._services = services
        return services

    def service(self, name: str) -> Tr064Service:
        wanted = name.casefold()
        matches = [
            item
            for item in self.discover()
            if item.service_type.casefold() == wanted
            or item.service_id.casefold() == wanted
            or wanted in item.service_type.casefold()
        ]
        if not matches:
            raise ValueError(f"servicio TR-064 no disponible: {name}")
        return matches[-1]

    def call(
        self, service_name: str, action: str, arguments: dict[str, object] | None = None
    ) -> dict[str, str]:
        service = self.service(service_name)
        action_tag = f"{{{service.service_type}}}{action}"
        envelope = ET.Element(f"{{{SOAP_ENV}}}Envelope")
        envelope.set(f"{{{SOAP_ENV}}}encodingStyle", "http://schemas.xmlsoap.org/soap/encoding/")
        body = ET.SubElement(envelope, f"{{{SOAP_ENV}}}Body")
        action_node = ET.SubElement(body, action_tag)
        for key, value in (arguments or {}).items():
            ET.SubElement(action_node, key).text = str(value)
        payload = ET.tostring(envelope, encoding="utf-8", xml_declaration=True)
        request = Request(
            urljoin(self.base_url, service.control_url.lstrip("/")),
            data=payload,
            headers={
                "Content-Type": 'text/xml; charset="utf-8"',
                "SOAPAction": f'"{service.service_type}#{action}"',
            },
            method="POST",
        )
        raw = self._open(request)
        try:
            root = ET.parse(BytesIO(raw)).getroot()
        except ET.ParseError as error:
            raise ValueError("TR-064 devolvió una respuesta SOAP inválida") from error

        fault = next(
            (node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "Fault"),
            None,
        )
        if fault is not None:
            values = {
                node.tag.rsplit("}", 1)[-1]: (node.text or "").strip()
                for node in fault.iter()
                if node.text and node.text.strip()
            }
            detail = values.get("errorDescription") or values.get("faultstring") or "error SOAP"
            code = values.get("errorCode")
            raise ValueError(f"TR-064 {detail}" + (f" ({code})" if code else ""))

        response_name = f"{action}Response"
        response = next(
            (
                node
                for node in root.iter()
                if node.tag.rsplit("}", 1)[-1] == response_name
            ),
            None,
        )
        if response is None:
            raise ValueError(f"TR-064 no devolvió {response_name}")
        return {
            child.tag.rsplit("}", 1)[-1]: (child.text or "").strip()
            for child in response
        }
