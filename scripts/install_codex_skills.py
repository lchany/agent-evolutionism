#!/usr/bin/env python3
"""Backward-compatible wrapper for install_agent_skills.py."""

from __future__ import annotations

import runpy
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_agent_skills.py")


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
