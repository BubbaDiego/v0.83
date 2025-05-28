import json
import os
from pathlib import Path
from typing import Dict, Iterable


class Persona:
    """Simple persona container."""

    def __init__(self, data: Dict):
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.strategy_weights = data.get("strategy_weights", {})
        self.instructions = data.get("instructions", "")


class PersonaManager:
    """Load and retrieve personas."""

    def __init__(self):
        self._personas: Dict[str, Persona] = {}
        self._load_builtin()

    def _load_builtin(self):
        base = Path(__file__).with_name("personas")
        if base.is_dir():
            for path in base.glob("*.json"):
                self.load_from_file(path)

    def load(self, personas: Iterable[Dict]):
        for data in personas:
            self.register(data)

    def load_from_file(self, path: str):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "name" in data:
            self.register(data)
        elif isinstance(data, list):
            self.load(data)

    def register(self, data: Dict):
        persona = data if isinstance(data, Persona) else Persona(data)
        self._personas[persona.name] = persona

    def get(self, name: str) -> Persona:
        if name not in self._personas:
            raise KeyError(name)
        return self._personas[name]

    def list_personas(self):
        return list(self._personas.keys())
