#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    test_file = Path(__file__).resolve().with_name("test_debate_e2e.py")

    env = os.environ.copy()
    env["PLAYWRIGHT_HEADED"] = "1"
    env.setdefault("E2E_SERVER_URL", "http://127.0.0.1:8081")

    cmd = [sys.executable, "-m", "pytest", str(test_file), "-s"]
    return subprocess.call(cmd, cwd=repo_root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
