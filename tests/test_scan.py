import unittest

from app.services.element_scanner import parse_ports, scan_tcp_ports


class _FakeSocket:
    def __init__(self, banner=b""):
        self.banner = banner
        self.closed = False

    def settimeout(self, _timeout):
        pass

    def recv(self, _size):
        return self.banner

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


if __name__ == "__main__":
    unittest.main()
