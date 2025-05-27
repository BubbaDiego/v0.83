#!/usr/bin/env python3
"""Run an end-to-end Playwright test using the Phantom wallet extension.

This script exercises the ``AutoCore`` automation helpers outside of pytest.
It simply deposits (or withdraws) a small amount of collateral on Jupiter
using Playwright with the Phantom extension loaded.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    def load_dotenv(*_a, **_k):
        return False

# Ensure repository root is on the import path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Automatically load environment variables if available
load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env.example")



def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "y", "on"}


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run AutoCore E2E workflow with Playwright and Phantom",
    )
    parser.add_argument(
        "--phantom-path",
        default=os.getenv("PHANTOM_PATH"),
        help="Path to Phantom extension (env PHANTOM_PATH)",
    )
    parser.add_argument(
        "--profile-dir",
        default=os.getenv("PW_PROFILE_DIR", "/tmp/playwright-profile"),
        help="Persistent browser profile directory (env PW_PROFILE_DIR)",
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=float(os.getenv("AUTOCORE_AMOUNT", "0.01")),
        help="Collateral amount to use (env AUTOCORE_AMOUNT)",
    )
    parser.add_argument(
        "--withdraw",
        action="store_true",
        default=_bool_env("AUTOCORE_WITHDRAW"),
        help="Run withdraw instead of deposit (env AUTOCORE_WITHDRAW)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=_bool_env("PW_HEADLESS"),
        help="Run browser in headless mode (env PW_HEADLESS)",
    )
    parser.add_argument(
        "--extension-id",
        default=os.getenv("PHANTOM_EXTENSION_ID"),
        help="Phantom extension ID (env PHANTOM_EXTENSION_ID)",
    )
    parser.add_argument(
        "--user-agent",
        default=os.getenv("PW_USER_AGENT"),
        help="Optional custom user agent (env PW_USER_AGENT)",
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=int(os.getenv("PW_SLOW_MO", "0")),
        help="Slow motion delay in ms (env PW_SLOW_MO)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    try:
        from auto_core import AutoCore
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"Playwright/AutoCore unavailable: {exc}")
        return 1

    core = AutoCore(
        args.phantom_path,
        args.profile_dir,
        headless=args.headless,
        extension_id=args.extension_id,
        user_agent=args.user_agent,
        slow_mo=args.slow_mo,
    )

    if args.withdraw:
        core.withdraw_collateral(args.amount)
    else:
        core.deposit_collateral(args.amount)

    print("✅ E2E workflow completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
