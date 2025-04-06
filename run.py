#!/usr/bin/env python
"""
Wrapper script to run the main module with the correct Python path.
"""
from src.main import main
import os
import sys
from pathlib import Path

# Get the project root directory
project_root = str(Path(__file__).resolve().parent)

# Add to Python path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import and run the main module

if __name__ == "__main__":
    main()
