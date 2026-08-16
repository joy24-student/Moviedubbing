#!/usr/bin/env python3
"""Convenient launcher for AI Movie Dubbing Studio Desktop App (Qt/PySide6)."""

import sys
from pathlib import Path

# Add src to python path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from aidub.ui.application import run_desktop

if __name__ == "__main__":
    print("=" * 65)
    print(" Starting AI Movie Dubbing Studio Desktop Application (Qt)...")
    print("=" * 65)
    sys.exit(run_desktop())
