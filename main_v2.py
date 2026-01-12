#!/usr/bin/env python3
"""
AI Debate Arena v2 - Multi-Debater Edition
"Hi, Super Nintendo Chalmers!" - Ralph Wiggum

Run with: python main_v2.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from server_v2 import main

if __name__ == "__main__":
    asyncio.run(main())
