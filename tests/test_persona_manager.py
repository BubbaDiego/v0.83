import importlib


def test_persona_manager_loading():
    pm_mod = importlib.import_module("oracle_core.persona_manager")
    manager = pm_mod.PersonaManager()
    personas = manager.list_personas()
    assert "selena" in personas
    persona = manager.get("selena")
    assert isinstance(persona.weights, dict)
    assert persona.get_weight("safe") == 0.7
