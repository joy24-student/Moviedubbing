#!/usr/bin/env python3
"""Convenient launcher for AI Movie Dubbing Studio Web UI."""

import sys
from pathlib import Path

# Add src to python path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from aidub.ui.web_ui import launch_web_ui

if __name__ == "__main__":
    print("=" * 65)
    print(" Starting AI Movie Dubbing Studio Interactive Web UI...")
    print(" Open http://localhost:7860 in your browser to test manually.")
    print("=" * 65)
    launch_web_ui(port=7860)
