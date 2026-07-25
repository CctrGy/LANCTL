import argparse
import io
import unittest
from unittest.mock import patch

from colorama import Fore, Style

from app.cli import build_parser
from app.core.parser import LANCTLArgumentParser


def all_parsers(root):
    pending = [root]
    seen = set()
    while pending:
        parser = pending.pop()
        if id(parser) in seen:
            continue
        seen.add(id(parser))
        yield parser
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                pending.extend(action.choices.values())


class TtyBuffer(io.StringIO):
    def isatty(self):
        return True


class HelpTests(unittest.TestCase):
    def test_every_parser_uses_the_standard_help_shape(self):
        parsers = list(all_parsers(build_parser()))
        self.assertGreaterEqual(len(parsers), 20)
        for parser in parsers:
            with self.subTest(prog=parser.prog):
                self.assertIsInstance(parser, LANCTLArgumentParser)
                help_text = parser.format_help()
                self.assertTrue(help_text.startswith("Uso: "))
                self.assertIn("Opciones:", help_text)
                self.assertNotIn("usage:", help_text)
                self.assertNotIn("positional arguments:", help_text)
                self.assertNotIn("options:", help_text)
                self.assertNotIn("==SUPPRESS==", help_text)

    def test_tty_help_uses_the_common_palette(self):
        stream = TtyBuffer()
        with patch("app.core.parser.sys.stdout", stream):
            help_text = build_parser().format_help()
        self.assertIn(Style.BRIGHT + Fore.CYAN + "Uso:", help_text)
        self.assertIn(Style.BRIGHT + Fore.YELLOW + "Argumentos:", help_text)
        self.assertIn(Fore.CYAN + "-h,", help_text)

    def test_no_visible_argument_lacks_help_text(self):
        for parser in all_parsers(build_parser()):
            for action in parser._actions:
                if isinstance(action, argparse._SubParsersAction):
                    continue
                with self.subTest(prog=parser.prog, dest=action.dest):
                    self.assertIsNotNone(action.help)


if __name__ == "__main__":
    unittest.main()
