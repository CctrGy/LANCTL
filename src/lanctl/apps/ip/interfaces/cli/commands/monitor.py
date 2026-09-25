"""Compatibility module: LANMON owns its command implementation."""

import sys

from lanctl.apps.monitor import commands

sys.modules[__name__] = commands
