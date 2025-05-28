import json
from pathlib import Path
from typing import Dict, Iterable


class Persona:
    """Container for strategy weighting definitions."""

    def __init__(self, name: str, weights: Dict[str, float]):
        self.name = name
        self.weights = weights

    def get_weight(self, strategy_name: str) -> float:
        return float(self.weights.get(strategy_name, 0.0))

    def weighted_strategies(self) -> Dict[str, float]:
        """Return the mapping of strategy names to weights."""
        return dict(self.weights)


class PersonaManager:
    """Load and manage persona definitions."""

    def __init__(self):
        self._personas: Dict[str, Persona] = {}
        self._load_builtin()

    def _load_builtin(self):
        base = Path(__file__).with_name("personas")
        if not base.is_dir():
            return
        for path in base.glob("*.json"):
            try:
                self.load_from_file(path)
            except Exception:
                continue

    def load(self, personas: Iterable[Dict[str, float]]):
        for name, weights in personas:
            self.register(name, weights)

    def load_from_file(self, path: str | Path):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return
        name = Path(path).stem
        self.register(name, data)

    def register(self, name: str, weights: Dict[str, float]):
        persona = Persona(name, weights)
        self._personas[name] = persona

    def get(self, name: str) -> Persona:
        if name not in self._personas:
            raise KeyError(name)
        return self._personas[name]

    def list_personas(self) -> Iterable[str]:
        return list(self._personas.keys())
