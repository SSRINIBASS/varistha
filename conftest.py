"""Root conftest.py — adds src paths to sys.path for all workspace packages."""

import sys
from pathlib import Path

# Add all package src roots to the path so tests can import them directly
_roots = [
    Path(__file__).parent / "apps" / "api" / "src",
    Path(__file__).parent / "apps" / "worker" / "src",
    Path(__file__).parent / "packages" / "cli" / "src",
    Path(__file__).parent / "packages" / "spec" / "src",
    Path(__file__).parent / "packages" / "sdk" / "src",
    Path(__file__).parent / "plugins",
]
for _root in _roots:
    _str = str(_root)
    if _str not in sys.path:
        sys.path.insert(0, _str)
