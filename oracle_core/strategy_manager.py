import json
from typing import Dict, Iterable


class Strategy:
    """Simple strategy container."""

    def __init__(self, data: Dict):
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.modifiers = data.get("modifiers", {})
        self.instructions = data.get("instructions", "")

    def apply(self, context: Dict) -> Dict:
        """Apply modifiers to the context. This minimal implementation just
        attaches the modifiers under ``strategy_modifiers``."""
        if not self.modifiers:
            return context
        new_ctx = dict(context)
        new_ctx["strategy_modifiers"] = self.modifiers
        return new_ctx


class StrategyManager:
    """Manage loading and retrieval of strategies."""

    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
        self._load_builtin()

    def _load_builtin(self):
        """Load strategies bundled with the package."""
        import os

        base = os.path.join(os.path.dirname(__file__), "strategies")
        if not os.path.isdir(base):  # pragma: no cover - defensive
            return
        for name in os.listdir(base):
            if name.endswith(".json"):
                try:
                    self.load_from_file(os.path.join(base, name))
                except Exception:
                    continue

    def load(self, strategies: Iterable[Dict]):
        for data in strategies:
            self.register(data)

    def load_from_file(self, path: str):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "name" in data:
            self.register(data)
        elif isinstance(data, list):
            self.load(data)

    def register(self, data: Dict):
        strat = data if isinstance(data, Strategy) else Strategy(data)
        self._strategies[strat.name] = strat

    def get(self, name: str) -> Strategy:
        if name not in self._strategies:
            raise KeyError(name)
        return self._strategies[name]

    def list_strategies(self) -> Iterable[str]:
        """Return the names of all loaded strategies."""
        return list(self._strategies.keys())
