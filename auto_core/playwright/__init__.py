"""Playwright-based automation helpers for AutoCore."""

try:  # PhantomManager and others require Playwright at runtime
    from .phantom_manager import PhantomManager
    from .solflare_manager import SolflareManager
    from .jupiter_perps_flow import JupiterPerpsFlow
except Exception:  # pragma: no cover - optional dependency may be missing
    PhantomManager = None
    SolflareManager = None
    JupiterPerpsFlow = None

__all__ = [
    "PhantomManager",
    "SolflareManager",
    "JupiterPerpsFlow",
]
