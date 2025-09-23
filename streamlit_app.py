#!/usr/bin/env python3
"""
Streamlit entrypoint for Streamlit Cloud.
This thin wrapper ensures the app appears in the Main file selector.
"""
import os
from pathlib import Path

# Ensure working directory is repo root so relative paths (Reports/, etc.) work
os.chdir(Path(__file__).parent)

# Import the actual app (renders on import)
import ui_workflow  # noqa: F401


