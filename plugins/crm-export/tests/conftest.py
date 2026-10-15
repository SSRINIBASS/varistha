"""Pytest configuration for crm-export plugin tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Add plugins/crm-export directory to sys.path so modules can be imported
plugin_dir = Path(__file__).resolve().parents[1]
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))
