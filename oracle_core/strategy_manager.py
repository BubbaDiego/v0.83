import json
from pathlib import Path
from typing import Dict, Iterable, List


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
        strategies_dir = Path(__file__).with_name("strategies")
        if strategies_dir.is_dir():
            for path in strategies_dir.glob("*.json"):
                self.load_from_file(path)

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

    def list_strategies(self) -> List[str]:
        """Return the names of all loaded strategies."""
        return sorted(self._strategies.keys())
