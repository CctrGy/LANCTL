import unittest

from app.services.element_scanner import (
    identify_device,
    identify_tcp_service,
    parse_ports,
    scan_tcp_ports,
)


class _FakeSocket:
    def __init__(self, banner=b""):
        self.banner = banner
        self.closed = False

    def settimeout(self, _timeout):
        pass

    def recv(self, _size):
        return self.banner

    def sendall(self, _value):
        pass

    def close(self):
        self.closed = True


class ElementScannerTests(unittest.TestCase):
    def test_port_lists_and_ranges_are_normalized(self):
        self.assertEqual(parse_ports("443,80,8000-8002,80"), [80, 443, 8000, 8001, 8002])
        self.assertIn(22, parse_ports("common"))

    def test_invalid_or_excessive_port_ranges_are_rejected(self):
        for value in ("0", "65536", "100-20", "abc"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_ports(value)
        with self.assertRaises(ValueError):
            parse_ports("1-5000")

    def test_tcp_scanner_reports_only_open_ports_and_passive_banner(self):
        sockets = []

        def connector(address, timeout):
            self.assertGreater(timeout, 0)
            if address[1] != 22:
                raise ConnectionRefusedError
            sock = _FakeSocket(b"SSH-2.0-Test_Device\r\n")
            sockets.append(sock)
            return sock

        findings = scan_tcp_ports(
            "192.168.1.10", [22, 80], timeout=0.1, workers=2,
            banners=True, connector=connector,
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].port, 22)
        self.assertEqual(findings[0].service, "ssh")
        self.assertEqual(findings[0].banner, "SSH-2.0-Test_Device")
        self.assertTrue(sockets[0].closed)

    def test_rtsp_is_identified_by_response_instead_of_port_number(self):
        sock = _FakeSocket(b"RTSP/1.0 200 OK\r\nServer: CameraOS\r\n\r\n")
        finding = identify_tcp_service(
            "192.168.1.18", 443, 0.1,
            connector=lambda _address, timeout: sock,
        )
        self.assertEqual(finding.service, "rtsp")
        self.assertEqual(finding.product, "CameraOS")
        self.assertEqual(finding.confidence, "high")

    def test_http_is_identified_from_status_line_and_server_header(self):
        finding = identify_tcp_service(
            "192.168.1.20", 8080, 0.1,
            connector=lambda _address, timeout: _FakeSocket(
                b"HTTP/1.1 400 Bad Request\r\nServer: nginx\r\n\r\n"
            ),
        )
        self.assertEqual(finding.service, "http")
        self.assertEqual(finding.product, "nginx")

    def test_device_identification_reports_evidence_and_confidence(self):
        finding = identify_tcp_service(
            "192.168.1.18", 443, 0.1,
            connector=lambda _address, timeout: _FakeSocket(b"RTSP/1.0 200 OK\r\n"),
        )
        identified = identify_device([finding], "Hunan Fn-Link")
        self.assertEqual(identified.device_type, "camera")
        self.assertEqual(identified.confidence, "high")
        self.assertTrue(identified.evidence)


if __name__ == "__main__":
    unittest.main()
