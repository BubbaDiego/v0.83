import importlib


def test_persona_manager_merge():
    pm_mod = importlib.import_module("oracle_core.persona_manager")
    manager = pm_mod.PersonaManager()
    assert "wizard" in manager.list_personas()

    base = {"distanceWeight": 0.6, "leverageWeight": 0.3, "collateralWeight": 0.1}
    merged = manager.merge_modifiers(base, "wizard")
    assert merged["distanceWeight"] == 0.9
    assert merged["leverageWeight"] == 0.05
    assert merged["collateralWeight"] == 0.1
