import ipaddress
import unittest
from unittest.mock import MagicMock, patch

from lanctl.apps.ip.infrastructure.services.lan_scanner import local_ipv4


class LocalIPv4Tests(unittest.TestCase):
    def test_uses_route_to_requested_network_instead_of_default_route(self):
        sock = MagicMock()
        sock.getsockname.return_value = ("192.168.1.31", 49152)
        network = ipaddress.IPv4Network("192.168.1.0/24")

        with patch("socket.socket", return_value=sock):
            address = local_ipv4(network)

        sock.connect.assert_called_once_with(("192.168.1.1", 80))
        self.assertEqual(address, ipaddress.IPv4Address("192.168.1.31"))
        sock.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
