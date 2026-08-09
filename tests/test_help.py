import argparse
import io
import unittest
from unittest.mock import patch

from colorama import Fore, Style

from app.cli import build_parser
from app.core.parser import LANCTLArgumentParser
from app.i18n import t


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
    def test_help_uses_current_terminal_width(self):
        with patch("app.core.parser.terminal_columns", return_value=54):
            parser = build_parser()
            help_text = parser.format_help()
        # Los nombres canónicos con varios alias son tokens indivisibles.
        self.assertTrue(all(len(line) <= 60 for line in help_text.splitlines()))

    def test_every_parser_uses_the_standard_help_shape(self):
        parsers = list(all_parsers(build_parser()))
        self.assertGreaterEqual(len(parsers), 20)
        for parser in parsers:
            with self.subTest(prog=parser.prog):
                self.assertIsInstance(parser, LANCTLArgumentParser)
                help_text = parser.format_help()
                self.assertTrue(help_text.startswith(t("LANCTL.PARSER.SECTION.USAGE") + " "))
                self.assertIn(t("LANCTL.PARSER.SECTION.OPTIONS"), help_text)
                self.assertNotIn("usage:", help_text)
                self.assertNotIn("positional arguments:", help_text)
                self.assertNotIn("options:", help_text)
                self.assertNotIn("==SUPPRESS==", help_text)

    def test_tty_help_uses_the_common_palette(self):
        stream = TtyBuffer()
        with patch("app.core.parser.sys.stdout", stream):
            help_text = build_parser().format_help()
        self.assertIn(Style.BRIGHT + Fore.CYAN + t("LANCTL.PARSER.SECTION.USAGE"), help_text)
        self.assertIn(Style.BRIGHT + Fore.YELLOW + t("LANCTL.PARSER.SECTION.ARGUMENTS"), help_text)
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
