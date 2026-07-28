import unittest

from colorama import Fore

from app.terminals.ssh_color import colorize_ssh_output, terminal_theme


class SshColorTests(unittest.TestCase):
    def test_network_tokens_receive_semantic_colors(self):
        rendered = colorize_ssh_output(
            "Gi1/0/7 up 192.168.1.11 24:5E:BE:65:C0:EC\n", "cisco"
        )
        self.assertIn(Fore.LIGHTCYAN_EX, rendered)
        self.assertIn(Fore.LIGHTGREEN_EX, rendered)
        self.assertIn(Fore.LIGHTBLUE_EX, rendered)
        self.assertIn(Fore.LIGHTMAGENTA_EX, rendered)

    def test_remote_ansi_sequences_are_preserved(self):
        value = "\x1b[31mREMOTE\x1b[0m\n"
        self.assertEqual(colorize_ssh_output(value), value)

    def test_theme_follows_device_adapter(self):
        self.assertEqual(terminal_theme({"driver": "cisco_s300"}), "cisco")
        self.assertEqual(
            terminal_theme({"terminalAdapter": "esp32_rack_monitor"}), "esp"
        )


if __name__ == "__main__":
    unittest.main()
