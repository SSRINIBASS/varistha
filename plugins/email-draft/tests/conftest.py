"""Pytest configuration for email-draft plugin tests."""

import sys
from pathlib import Path

plugin_dir = Path(__file__).resolve().parents[1]
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))
