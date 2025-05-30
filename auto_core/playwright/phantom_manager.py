"""Re-export :class:`PhantomManager` from :mod:`..phantom_manager`."""

try:  # PhantomManager depends on Playwright at runtime
    from ..phantom_manager import PhantomManager
except Exception:  # pragma: no cover - optional dependency may be missing
    PhantomManager = None

__all__ = ["PhantomManager"]
