import importlib.util
from pathlib import Path
import sys


def load_module():
    base = Path(__file__).resolve().parents[1]
    oc_base = base / "oracle_core"

    ods_path = oc_base / "oracle_data_service.py"
    ods_spec = importlib.util.spec_from_file_location("oracle_core.oracle_data_service", ods_path)
    ods_mod = importlib.util.module_from_spec(ods_spec)
    assert ods_spec and ods_spec.loader
    ods_spec.loader.exec_module(ods_mod)
    sys.modules["oracle_core.oracle_data_service"] = ods_mod

    path = base / "oracle_core" / "oracle_core.py"
    spec = importlib.util.spec_from_file_location("oracle_core.oracle_core", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    sys.modules["oracle_core.oracle_core"] = module
    return module


def test_oracle_core_build_prompt(monkeypatch):
    mod = load_module()

    class DummyAlerts:
        def get_all_alerts(self):
            return ["a1"]

    class DummyPrices:
        def get_all_prices(self):
            return [1]

    class DummyPortfolio:
        def get_latest_snapshot(self):
            return {"id": "snap"}

    class DummyLocker:
        def __init__(self):
            self.alerts = DummyAlerts()
            self.prices = DummyPrices()
            self.portfolio = DummyPortfolio()

        def get_last_update_times(self):
            return {"x": 1}

    oc = mod.OracleCore(DummyLocker())
    assert "test" in oc.strategy_manager.list_strategies()
    monkeypatch.setattr(oc, "query_gpt", lambda messages: messages)
    messages = oc.ask("portfolio", "test")
    assert messages[0]["role"] == "system"
    assert messages[-1]["content"] == "do"
