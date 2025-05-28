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

    @staticmethod
    def merge_modifiers(weighted_mods: Iterable[tuple[Dict, float]]) -> Dict:
        """Merge multiple modifier dicts given (modifiers, weight) pairs."""

        def _merge(target: Dict, source: Dict, weight: float):
            for key, value in source.items():
                if isinstance(value, dict):
                    target.setdefault(key, {})
                    _merge(target[key], value, weight)
                elif isinstance(value, list):
                    target.setdefault(key, set())
                    target[key].update(value)
                elif isinstance(value, (int, float)):
                    total, w_sum = target.get(key, (0.0, 0.0))
                    target[key] = (total + value * weight, w_sum + weight)
                else:
                    cur_val, cur_w = target.get(key, (None, 0.0))
                    if cur_val is None or weight > cur_w:
                        target[key] = (value, weight)

        merged: Dict[str, object] = {}
        for mods, weight in weighted_mods:
            _merge(merged, mods, float(weight))

        def _finalize(value):
            if isinstance(value, dict):
                return {k: _finalize(v) for k, v in value.items()}
            if isinstance(value, set):
                return list(value)
            if isinstance(value, tuple):
                val, w = value
                if isinstance(val, (int, float)):
                    return val / w if w else val
                return val
            return value

        return {k: _finalize(v) for k, v in merged.items()}


class StrategyManager:
    """Manage loading and retrieval of strategies."""

    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
        self.aliases = {
            # allow older UI names to continue working
            "aggressive": "degen",
        }
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
        """Retrieve a strategy by name.

        Supports a small alias map so older front-ends can continue to
        request strategies using legacy names without raising ``KeyError``.
        """
        key = name
        if key not in self._strategies:
            key = self.aliases.get(name, name)
        if key not in self._strategies:
            raise KeyError(name)
        return self._strategies[key]

    def list_strategies(self) -> Iterable[str]:
        """Return the names of all loaded strategies."""
        return list(self._strategies.keys())

