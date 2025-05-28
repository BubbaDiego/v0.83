import json
import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class Persona:
    """Simple persona container."""

    name: str
    system_message: str = ""
    instructions: str = ""


class PersonaManager:
    """Load and retrieve persona definitions."""

    def __init__(self):
        self._personas: Dict[str, Persona] = {}
        self._load_builtin()
        # Always provide a fallback persona
        self._personas.setdefault("default", Persona("default"))

    def _load_builtin(self):
        base = os.path.join(os.path.dirname(__file__), "personas")
        if not os.path.isdir(base):
            return
        for fname in os.listdir(base):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(base, fname)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                continue
            name = data.get("name") or os.path.splitext(fname)[0]
            persona = Persona(
                name=name,
                system_message=data.get("system_message", ""),
                instructions=data.get("instructions", ""),
            )
            self._personas[name] = persona

    def get(self, name: str) -> Persona:
        if name not in self._personas:
            raise KeyError(name)
        return self._personas[name]
