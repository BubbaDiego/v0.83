from .auto_core import AutoCore
from . import phantom_workflow

try:  # PhantomManager requires Playwright
    from .phantom_manager import PhantomManager
except Exception:  # pragma: no cover - optional dependency may be missing
    PhantomManager = None

__all__ = ["AutoCore", "phantom_workflow", "PhantomManager"]
