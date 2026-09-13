import os
import unittest

from lanctl.core.command_line import split_command_line


class CommandLineTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "sintaxis específica de Windows")
    def test_windows_paths_keep_backslashes(self):
        path = r"C:\Users\Victor\Documents\LanCTL\home.vlf"
        self.assertEqual(split_command_line(f'project use "{path}"'), ["project", "use", path])

    def test_quoted_values_remain_one_argument(self):
        self.assertEqual(
            split_command_line('element NAS -description "Servidor principal"'),
            ["element", "NAS", "-description", "Servidor principal"],
        )
